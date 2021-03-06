import falcon
from falcon.testing import helpers
import mock
import unittest

from jumpgate import api
from jumpgate.compute.drivers.sl import extra_specs
from jumpgate.compute.drivers.sl import flavor_list_loader


TENANT_ID = 333333


def get_client_env(**kwargs):
    env = helpers.create_environ(**kwargs)
    return env


class TestExtraSpecsFlavor(unittest.TestCase):
    # Checks that all the optional parameters are sent in the response
    # and also error-checking for invalid flavor id

    def perform_extra_detail(self, tenant_id, flavor_id):
        env = get_client_env()
        self.req = api.Request(env)
        self.resp = falcon.Response()
        flavors = flavor_list_loader.Flavors.get_flavors(app=mock.MagicMock())
        instance = extra_specs.ExtraSpecsFlavorV2(app=mock.MagicMock(),
                                                  flavors=flavors)
        instance.on_get(self.req, self.resp, tenant_id, flavor_id)

    def test_on_get_for_all_details(self):
        # Testing on a valid flavor_id
        self.perform_extra_detail(TENANT_ID, 1)
        self.assertEqual(list(self.resp.body.keys()), ['extra_specs'])
        self.assertEqual(len(self.resp.body['extra_specs']), 1)

        # Checks that the 1 optional parameter (portspeed) is being sent in
        # response, and that no other parameter is in extra-specs
        self.assertIn('portspeed', self.resp.body['extra_specs'])
        self.assertNotIn('swap', self.resp.body['extra_specs'])
        self.assertNotIn('disk-type', self.resp.body['extra_specs'])
        self.assertNotIn('rxtx_factor', self.resp.body['extra_specs'])
        self.assertEqual(self.resp.status, 200)

    def test_on_get_for_out_of_range_flavor(self):
        # Testing on an out of range flavor_id
        self.perform_extra_detail(TENANT_ID, 23)
        self.assertEqual(self.resp.status, 400)

    def test_on_get_for_invalid_flavor(self):
        # Testing on an invalid (not an number) flavor_id
        self.perform_extra_detail(TENANT_ID, 'not a number')
        self.assertEqual(self.resp.status, 400)


class TestExtraSpecsFlavorKey(unittest.TestCase):
    # Checks that the appropriate optional parameter is sent when requested
    # and also error-checking for invalid flavor id and invalid key id

    def perform_extra_detail_key(self, tenant_id, flavor_id, key_id):
        env = get_client_env()
        self.req = api.Request(env)
        self.resp = falcon.Response()
        flavors = flavor_list_loader.Flavors.get_flavors(app=mock.MagicMock())
        instance = extra_specs.ExtraSpecsFlavorKeyV2(app=mock.MagicMock(),
                                                     flavors=flavors)
        instance.on_get(self.req, self.resp, tenant_id, flavor_id, key_id)

    def test_on_get_for_portspeed(self):
        # Testing for the 'portspeed' optional spec
        self.perform_extra_detail_key(TENANT_ID, 1, 'portspeed')
        self.assertEqual(list(self.resp.body.keys()), ['portspeed'])
        self.assertEqual(self.resp.status, 200)

    def test_on_get_for_invalid_flavor(self):
        # Testing for an invalid flavor id
        self.perform_extra_detail_key(TENANT_ID, 42, 'portspeed')
        self.assertEqual(self.resp.status, 400)

    def test_on_get_for_invalid_key(self):
        # Testing for a valid flavor id, but invalid key (optional spec)
        self.perform_extra_detail_key(TENANT_ID, 1, 'invalid_key')
        self.assertEqual(self.resp.status, 400)
