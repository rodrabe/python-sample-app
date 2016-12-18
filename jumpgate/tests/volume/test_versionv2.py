import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate.volume.drivers.sl import versionv2

base_volume_url = 'http://localhost:5000/volume/v2.0/'


def get_client_env(**kwargs):
    client = mock.MagicMock()
    env = helpers.create_environ(**kwargs)
    env['auth'] = {'tenant_id': 999999}
    return client, env


class TestVersionV2(unittest.TestCase):

    def check_response_body(self, version):

        self.assertEqual('v2.0', version['id'])
        self.assertEqual('CURRENT', version['status'])
        self.assertEqual("", version['min_version'])
        self.assertEqual("", version['version'])
        for link in version['links']:
            self.assertEqual('self', link['rel'])
            self.assertEqual(base_volume_url, link['href'],)

    def test_on_get_response(self):
        """Test working path of VolumeV2()"""
        client, env = get_client_env()

        req = falcon.Request(env)
        resp = falcon.Response()
        # Test with a tenant passed in;  tenant id is an optional parameter;
        # this would happen when the nova client is used

        self.app = mock.MagicMock()
        self.app.get_endpoint_url.return_value = base_volume_url
        version2_object = versionv2.VersionV2(app=self.app)
        version2_object.on_get(req, resp, "99999")

        self.check_response_body(resp.body['version'])
        # Now test with NO tenant passed in
        version2_object.on_get(req, resp)

        self.check_response_body(resp.body['version'])
        self.assertEqual('200 OK', resp.status)
