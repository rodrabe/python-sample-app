import unittest

import falcon
import mock

from jumpgate.network.drivers.sl import index
from jumpgate.tests.network import utils

base_network_url = 'http://localhost:5000/network/v2.0'


def get_client_env(**kwargs):
    client = mock.MagicMock()
    client.get_endpoint_url.return_value = base_network_url
    return client, utils.get_env(client, **kwargs)


class TestIndex(unittest.TestCase):

    def check_response_body(self, resp_body_index):
        for element in resp_body_index:
            if element['id'] == 'v2.0':
                self.assertEqual(element['status'], 'CURRENT')
                for link in element['links']:
                    if link['rel'] == 'self':
                        self.assertEqual(link['href'], base_network_url)
                    else:
                        self.fail("Invalid link returned")
            else:
                self.fail("Invalid version returned")

    def test_on_get_response(self):
        """Test working path of NetworkV2()"""
        client, env = get_client_env(query_string='name=123321')

        req = falcon.Request(env)
        resp = falcon.Response()

        index.Index(client).on_get(req, resp)

        self.check_response_body(resp.body['versions'])
        self.assertEqual(resp.status, '200 OK')
