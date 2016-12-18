import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate.volume.drivers.sl import index

# FIXME(mriedem): Need to run the actual wsgi service in a fixture.
base_url = 'http://localhost:5000/volume/v2'


def get_client_env(**kwargs):
    client = mock.MagicMock()
    env = helpers.create_environ(**kwargs)
    env['auth'] = {'tenant_id': 999999}
    return client, env


class TestIndex(unittest.TestCase):

    def check_response_body(self, resp_body_index):
        for element in resp_body_index:
            self.assertEqual('v2.0', element['id'])
            self.assertEqual('CURRENT', element['status'])
            for link in element['links']:
                self.assertEqual('self', link['rel'])
                self.assertEqual(base_url, link['href'])

    def test_on_get_response(self):
        """Test working path of VolumeV2()"""
        client, env = get_client_env()

        req = falcon.Request(env)
        resp = falcon.Response()
        self.app = mock.MagicMock()
        self.app.get_endpoint_url.return_value = base_url
        index_object = index.Index(app=self.app)

        index_object.on_get(req, resp)

        self.check_response_body(resp.body['versions'])
        self.assertEqual(resp.status, '200 OK')
