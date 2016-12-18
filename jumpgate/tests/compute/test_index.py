import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate import api
from jumpgate.compute.drivers.sl import index

base_url = 'http://localhost:5000/compute/'


def get_client_env():
    env = helpers.create_environ()
    env['auth'] = {'tenant_id': 999999}
    return env


class TestIndex(unittest.TestCase):

    def check_response_body(self, resp_body_index):
        self.assertEqual(1, len(resp_body_index))
        for element in resp_body_index:
            self.assertEqual('v2.0', element['id'])
            self.assertEqual('CURRENT', element['status'])
            self.assertEqual('2011-01-21T11:33:21Z', element['updated'])
            for link in element['links']:
                self.assertEqual('self', link['rel'])
                self.assertEqual(base_url, link['href'])

    def test_on_get_response(self):
        """Test working path of ComputeV2()"""
        env = get_client_env()

        req = api.Request(env)
        resp = falcon.Response()
        app = mock.MagicMock()
        app.get_endpoint_url.return_value = base_url
        index_object = index.IndexV2(app=app)

        index_object.on_get(req, resp)

        self.check_response_body(resp.body['versions'])
        self.assertEqual(resp.status, '200 OK')
