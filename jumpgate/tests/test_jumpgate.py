import falcon
import mock
import unittest

from jumpgate import api
from jumpgate.common import dispatcher
from jumpgate.common.hooks import core


class StubResource(object):
    pass


TEST_CFG = {
    'compute': {'driver': 'path.to.compute.driver',
                'mount': '/compute'},
    'identity': {'driver': 'path.to.identity.driver', 'mount': None},
    'enabled_services': ['compute', 'identity']
}


class TestJumpgateInit(unittest.TestCase):
    def test_init(self):
        app = api.Jumpgate()

        self.assertEqual(app.installed_modules, {})

        self.assertIsInstance(app.before_hooks, list)
        self.assertIsInstance(app.after_hooks, list)
        self.assertEqual(app.before_hooks, [core.hook_set_uuid])
        self.assertEqual(app.after_hooks, [core.hook_format])

        self.assertEqual(app._dispatchers, {})


class TestJumpgate(unittest.TestCase):
    def setUp(self):
        self.config = mock.MagicMock()
        self.app = api.Jumpgate()

    def test_make_api(self):
        # Populate a dispatcher with some resources
        disp = dispatcher.Dispatcher()
        resources = [StubResource() for i in range(10)]
        for i, resource in enumerate(resources):
            disp.add_endpoint('test_%s' % i, '/path/to/%s' % i)
            disp.set_handler('test_%s' % i, resource)

        self.app.add_dispatcher('SERVICE', disp)

        api = self.app.make_api()
        self.assertTrue(hasattr(api, '__call__'))
        self.assertIsInstance(api, falcon.API)
        self.assertEqual(len(api._routes), 20)

    def test_add_get_dispatcher(self):
        disp = dispatcher.Dispatcher()
        self.app.add_dispatcher('SERVICE', disp)

        self.assertEqual(self.app._dispatchers, {'SERVICE': disp})

        disp_return = self.app.get_dispatcher('SERVICE')
        self.assertEqual(disp_return, disp)

    def test_get_endpoint_url(self):
        disp = dispatcher.Dispatcher()
        disp.add_endpoint('user_page0', '/path0/to/{tenant_id}')
        self.app.add_dispatcher('SERVICE', disp)

        req = mock.MagicMock()
        req.env = {'tenant_id': '1234'}
        req.protocol = 'http'
        req.get_header.return_value = 'some_host'
        req.app = ''

        url = self.app.get_endpoint_url('SERVICE', req, 'user_page0')
        self.assertEqual(url, 'http://some_host/path0/to/1234')

    @mock.patch('jumpgate.api.importlib.import_module')
    def test_load_drivers(self, import_module):
        compute_disp = mock.MagicMock()
        identity_disp = mock.MagicMock()
        self.app._dispatchers = {'compute': compute_disp,
                                 'identity': identity_disp}

        self.app.config = TEST_CFG
        self.app.load_drivers()

        # Make sure setup_routes() is called for each driver. Order
        # is ignored due to Python 3's different dict ordering
        import_module.assert_has_calls([
            mock.call('path.to.compute.driver'),
            mock.call().setup_routes(self.app, compute_disp),
            mock.call('path.to.identity.driver'),
            mock.call().setup_routes(self.app, identity_disp),
        ], any_order=True)

    def test_load_endpoints(self):
        self.app.config = TEST_CFG
        self.app.load_endpoints()

        self.assertEqual(len(self.app._dispatchers), 2)
        self.assertEqual(sorted(self.app._dispatchers.keys()),
                         sorted(['compute', 'identity']))

        self.assertEqual(self.app.installed_modules,
                         {'baremetal': False,
                          'compute': True,
                          'identity': True,
                          'image': False,
                          'network': False,
                          'volume': False})
