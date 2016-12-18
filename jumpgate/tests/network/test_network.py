import unittest

import falcon
import mock

from jumpgate import api
from jumpgate.network.drivers.sl import networks
from jumpgate.tests.network import utils


TENANT_ID = 999999


def get_client_env(**kwargs):
    client = mock.MagicMock()
    return client, utils.get_env(client, tenant_id=TENANT_ID, **kwargs)


def get_fake_net(network='PUBLIC'):
    return {'id': 11,
            'name': 'Public Network',
            'subnets': [{'id': 1},
                        {'id': 3},
                        {'id': 5}],
            'vlanNumber': 999,
            'networkSpace': network}


class TestNetworkV2(unittest.TestCase):

    def test_on_get_response_networkv2_public(self):
        """Test working path of NetworkV2()"""
        client, env = get_client_env(query_string='name=123321')

        net_vlan = client['Network_Vlan']
        fake_net = get_fake_net()
        net_vlan.getObject.return_value = fake_net
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworkV2().on_get(req, resp, fake_net['id'])
        self.assertEqual(resp.body['network'],
                         networks.format_network(fake_net,
                                                 TENANT_ID))
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body['network']['provider:physical_network'],
                         False)

    def test_on_get_response_networkv2_private(self):
        """Test working path of NetworkV2()"""

        client, env = get_client_env(query_string='name=123321')
        net_vlan = client['Network_Vlan']
        vlan = get_fake_net(network='PRIVATE')
        net_vlan.getObject.return_value = vlan
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworkV2().on_get(req, resp, vlan['id'])

        self.assertEqual(resp.body['network'],
                         networks.format_network(vlan, TENANT_ID))
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body['network']['provider:physical_network'],
                         True)

    def test_on_get_response_networkv2_invalid_id(self):
        """Test invalid id"""
        client, env = get_client_env()

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworkV2().on_get(req, resp, 'BAD_ID')
        self.assertEqual(resp.status, 400)


class TestNetworksV2(unittest.TestCase):

    def test_on_get_response_networksv2_show(self):
        """Test show function in NetworksV2"""

        client, env = get_client_env(query_string='name=123321')
        account = client['Account']
        fake_net = get_fake_net(network='PRIVATE')
        account.getNetworkVlans.return_value = [fake_net]

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworksV2().on_get(req, resp)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body['networks'][0],
                         networks.format_network(fake_net, TENANT_ID))

    def test_on_get_response_networksv2_show_no_match(self):
        """Test show function in NetworksV2 with no matching ID"""

        client, env = get_client_env(query_string='name=123321')
        client['Account'].getNetworkVlans.return_value = []

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworksV2().on_get(req, resp)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body['networks'], [])

    def test_on_get_response_networksv2_list_no_filter(self):
        # Verify that a list with no filter will return all of the
        # networks from getNetworkVlans along with the placeholder
        # public and private networks
        client, env = get_client_env()
        fake_net = get_fake_net(network='PRIVATE')
        client['Account'].getNetworkVlans.return_value = [fake_net]

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworksV2().on_get(req, resp)

        nets = [fake_net] + networks.VLANS.values()
        expected = [networks.format_network(net, TENANT_ID) for net in nets]

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['networks']), 3)
        # Assert that we have 3 networks: the fake network,
        # public placeholder network, and the private placeholder network
        self.assertItemsEqual(resp.body['networks'], expected)

    def test_on_get_response_networksv2_list_with_filter(self):
        """Test list function"""

        client, env = get_client_env(query_string='name=123321')
        fake_net = get_fake_net(network='PRIVATE')
        client['Account'].getNetworkVlans.return_value = [fake_net]

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworksV2().on_get(req, resp)
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['networks']), 1)
        self.assertEqual(resp.body['networks'][0],
                         networks.format_network(fake_net, TENANT_ID))

    def test_on_get_response_networksv2_list_filter_public(self):
        client, env = get_client_env(query_string='name=public')
        client['Account'].getNetworkVlans.return_value = []

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworksV2().on_get(req, resp)
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['networks']), 1)
        self.assertEqual(
            resp.body['networks'][0],
            networks.format_network(networks.VLANS['public'],
                                    TENANT_ID))

    def test_on_get_response_networksv2_list_filter_private(self):
        client, env = get_client_env(query_string='name=private')
        client['Account'].getNetworkVlans.return_value = []

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        networks.NetworksV2().on_get(req, resp)
        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['networks']), 1)
        self.assertEqual(
            resp.body['networks'][0],
            networks.format_network(networks.VLANS['private'],
                                    TENANT_ID))
