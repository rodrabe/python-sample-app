import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate import api
from jumpgate.compute.drivers.sl import images
from jumpgate.image.drivers.sl import images as glance_images

FAKE_IMAGE_GUID = 'a2c732dd-9635-4185-9204-fc8562cf0454'
FAKE_SELF_LINK = ('http://jumpgate.ibm.com:5000/compute/v2/9999/images/%s' %
                  FAKE_IMAGE_GUID)


def get_client_env():
    client = mock.MagicMock()
    env = helpers.create_environ()
    env['auth'] = {'tenant_id': 999999}
    return client, env


class TestComputeImageShow(unittest.TestCase):

    def test_on_get_response(self):
        """Basic test for the compuate image show proxy."""
        client, env = get_client_env()

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        app = mock.MagicMock()
        show_controller = images.ComputeImageShow(app)

        def fake_image_get(req, resp, image_id, tenant_id=None):
            resp.status = 200
            resp.body = {
                "size": "74185822",
                "created": "2011-01-01T01:02:03Z",
                "id": image_id,
                "links": [
                    {
                        "href": FAKE_SELF_LINK,
                        "rel": "self"
                    },
                ],
                "metadata": {},
                "min_disk": 0,
                "min_ram": 0,
                "name": "fakeimage7",
                "progress": 100,
                "status": "active",
                "updated": "2011-01-01T01:02:03Z"
            }

        with mock.patch.object(glance_images.ImageV2, 'on_get',
                               side_effect=fake_image_get) as image_show_mock:
            show_controller.on_get(req, resp, FAKE_IMAGE_GUID)

        image_show_mock.assert_called_once_with(
            req, resp, FAKE_IMAGE_GUID, None)

        self.assertEqual(200, resp.status)

        self.assertIn('image', resp.body)
        image = resp.body['image']
        expected_image = {
            "OS-EXT-IMG-SIZE:size": "74185822",
            "created": "2011-01-01T01:02:03Z",
            "id": FAKE_IMAGE_GUID,
            "links": [
                {
                    "href": FAKE_SELF_LINK,
                    "rel": "self"
                },
            ],
            "metadata": {},
            "minDisk": 0,
            "minRam": 0,
            "name": "fakeimage7",
            "progress": 100,
            "status": 'ACTIVE',
            "updated": "2011-01-01T01:02:03Z"
        }
        self.assertDictEqual(expected_image, image)

    def test_on_get_response_non_200_status_code_from_imagev2(self):
        """Tests that non-200 imagev2 response isn't processed."""
        client, env = get_client_env()

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        app = mock.MagicMock()
        show_controller = images.ComputeImageShow(app)

        def fake_image_get(req, resp, image_id, tenant_id=None):
            resp.status = 404
            resp.body = mock.sentinel.fail_body

        with mock.patch.object(glance_images.ImageV2, 'on_get',
                               side_effect=fake_image_get) as image_show_mock:
            show_controller.on_get(req, resp, FAKE_IMAGE_GUID)

        image_show_mock.assert_called_once_with(
            req, resp, FAKE_IMAGE_GUID, None)

        # Assert that the response wasn't modified.
        self.assertEqual(404, resp.status)
        self.assertEqual(mock.sentinel.fail_body, resp.body)
