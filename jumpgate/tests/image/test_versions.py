import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate.image.drivers.sl import versions

base_url = 'http://localhost:5000/image/'


def get_client_env():
    env = helpers.create_environ()
    env['auth'] = {'tenant_id': 999999}
    return env


class TestIndex(unittest.TestCase):

    def _validate_version(self, version, expected_id, expected_status):
        expected_keys = ['id', 'links', 'status']
        self.assertEqual(expected_keys, sorted(version.keys()))
        self.assertEqual(expected_id, version['id'])
        links = version['links']
        # should be a single link to itself
        self.assertEqual(1, len(links))
        link = links[0]
        self.assertEqual('self', link['rel'])
        # FIXME(mriedem): this isn't actually correct for the href but we can't
        # test this until we have a wsgi fixture for the app.
        self.assertEqual(base_url, link['href'])
        self.assertEqual(expected_status, version['status'])

    def test_on_get_response(self):
        """Test the root version index handler."""
        env = get_client_env()

        req = falcon.Request(env)
        resp = falcon.Response()
        app = mock.MagicMock()
        app.get_endpoint_url.return_value = base_url
        index_object = versions.Index(app=app)

        index_object.on_get(req, resp)

        self.assertEqual(resp.status, '200 OK')

        # We should have 2 versions
        indexed_versions = resp.body['versions']
        self.assertEqual(2, len(indexed_versions))
        # v2.0 comes first
        self._validate_version(indexed_versions[0], 'v2.0', 'CURRENT')
        # v1.0 comes next
        self._validate_version(indexed_versions[1], 'v1.0', 'SUPPORTED')


# TODO(mriedem): Test the image/v1/ route handler with a wsgi fixture to verify
# is routes to listing images with the image v1 API.
