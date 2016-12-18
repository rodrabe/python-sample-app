import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate import api
from jumpgate.compute.drivers.sl import versionv2

base_compute_url = 'http://localhost:5000/compute/v2.0/'


def get_client_env():
    env = helpers.create_environ()
    env['auth'] = {'tenant_id': 999999}
    return env


class TestVersionV2(unittest.TestCase):

    def check_response_body(self, version):
        self.assertEqual('2011-01-21T11:33:21Z', version['updated'])
        self.assertEqual('v2.0', version['id'])
        self.assertEqual('CURRENT', version['status'])
        self.assertEqual('', version['min_version'])
        self.assertEqual('', version['version'])
        self.assertEqual(1, len(version['links']))
        for link in version['links']:
            self.assertEqual('self', link['rel'])
            self.assertEqual(base_compute_url, link['href'],)

    def test_on_get_response(self):
        """Test working path of ComputeV2()"""
        env = get_client_env()

        req = api.Request(env)
        resp = falcon.Response()
        # Test with a tenant passed in;  tenant id is an optional parameter;
        # this would happen when the nova client is used

        self.app = mock.MagicMock()
        self.app.get_endpoint_url.return_value = base_compute_url
        version2_object = versionv2.VersionV2(app=self.app)
        version2_object.on_get(req, resp, "99999")

        self.check_response_body(resp.body['version'])
        # Now test with NO tenant passed in
        version2_object.on_get(req, resp)

        self.check_response_body(resp.body['version'])
        self.assertEqual(resp.status, '200 OK')
