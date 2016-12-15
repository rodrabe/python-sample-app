import unittest

import falcon
import mock

from jumpgate.network.drivers.sl import versionv2
from jumpgate.tests.network import utils

subnet_url = 'http://localhost:5000/network/v2.0/subnets'
networks_url = 'http://localhost:5000/network/v2.0/networks'


def side_effect(service, req, url):
    if url == 'v2_subnets':
        return subnet_url
    elif url == 'v2_networks':
        return networks_url
    else:
        raise Exception('Invalid URL requested')


def get_client_env(**kwargs):
    client = mock.MagicMock()
    client.get_endpoint_url.side_effect = side_effect
    return client, utils.get_env(client, **kwargs)


class TestVersionV2(unittest.TestCase):

    def check_response_body(self, resp_body_index):
        for element in resp_body_index:
            if element['name'] == 'subnet':
                self.assertEqual(element['collection'], 'subnets')
                for link in element['links']:
                    if link['rel'] == 'self':
                        self.assertEqual(link['href'], subnet_url)
                    else:
                        self.fail("Invalid link returned")
            elif element['name'] == 'network':
                self.assertEqual(element['collection'], 'networks')
                for link in element['links']:
                    if link['rel'] == 'self':
                        self.assertEqual(link['href'], networks_url)
                    else:
                        self.fail("Invalid link returned")
            else:
                self.fail("Invalid resource returned")

    def test_on_get_response(self):
        """Test working path of NetworkV2()"""
        client, env = get_client_env(query_string='name=123321')

        req = falcon.Request(env)
        resp = falcon.Response()

        versionv2.VersionV2(client).on_get(req, resp)

        self.check_response_body(resp.body['resources'])
        self.assertEqual(resp.status, '200 OK')
