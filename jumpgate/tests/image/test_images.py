import mock
import unittest

import falcon
from falcon.testing import helpers
import SoftLayer

from jumpgate import api
from jumpgate.image.drivers.sl import images


def get_client_env(**kwargs):
    client = mock.MagicMock()
    env = helpers.create_environ(**kwargs)
    return client, env


class TestImageV1(unittest.TestCase):

    def setUp(self):
        self.app = mock.MagicMock()

    def test_on_get(self):
        client, env = get_client_env()
        vgbdtg = client['Virtual_Guest_Block_Device_Template_Group']
        vgbdtg.getObject.return_value = {
            'globalIdentifier': 'uuid',
            'blockDevicesDiskSpaceTotal': 1000,
            'name': 'some image',
            'status': {'keyName': 'ACTIVE', 'name': 'Active'},
        }

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        images.ImageV1(self.app).on_get(req, resp, '1')

        image = resp.body['image']
        self.assertEqual(image['id'], 'uuid')
        self.assertEqual(image['name'], 'some image')
        self.assertEqual(image['size'], 1000)
        self.assertEqual('active', image['status'])

    def test_on_get_fail(self):
        client, env = get_client_env()
        vgbdtg = client['Virtual_Guest_Block_Device_Template_Group']
        error = SoftLayer.SoftLayerAPIError(
            "SoftLayer_Exception_ObjectNotFound",
            "Unable to find object with id of '1'")
        vgbdtg.getObject.side_effect = error

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        self.assertRaises(SoftLayer.SoftLayerAPIError,
                          images.ImageV1(self.app).on_get, req, resp, '1')

    def test_get_v1_image_details_dict(self):
        expected_keys = [
            'status',
            'updated',
            'created',
            'id',
            'progress',
            'metadata',
            'size',
            'OS-EXT-IMG-SIZE:size',
            'container_format',
            'disk_format',
            'is_public',
            'protected',
            'owner',
            'min_disk',
            'min_ram',
            'name',
            'links',
        ]
        app, req, image, tenant_id = (mock.MagicMock(),
                                      mock.MagicMock(),
                                      mock.MagicMock(),
                                      mock.MagicMock())
        res = images.get_v1_image_details_dict(app, req, image, tenant_id)
        self.assertEqual(set(expected_keys), set(res.keys()))

    def test_get_v1_image_details_dict_fail(self):
        app, req, image, tenant_id = (mock.MagicMock(),
                                      mock.MagicMock(),
                                      None,
                                      mock.MagicMock())
        res = images.get_v1_image_details_dict(app, req, image, tenant_id)
        self.assertFalse(res)


class TestImageV2(unittest.TestCase):

    def setUp(self):
        self.app = mock.MagicMock()

    def test_on_get(self):
        client, env = get_client_env()
        vgbdtg = client['Virtual_Guest_Block_Device_Template_Group']
        vgbdtg.getObject.return_value = {
            'globalIdentifier': 'uuid',
            'blockDevicesDiskSpaceTotal': 1000,
            'name': 'some image',
            'status': {'keyName': 'ACTIVE', 'name': 'Active'},
        }
        client['Account'].getPrivateBlockDeviceTemplateGroups.return_value = [{
            'globalIdentifier': 'uuid2',
            'blockDevicesDiskSpaceTotal': 2000,
            'name': 'some other image',
            'status': {'keyName': 'DEPRECATED', 'name': 'Deprecated'},
        }]

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        images.ImageV2(self.app).on_get(req, resp, 'uuid')

        self.assertEqual(resp.status, 200)
        image = resp.body
        self.assertEqual(image['id'], 'uuid')
        self.assertEqual(image['name'], 'some image')
        self.assertEqual(image['size'], 1000)
        self.assertEqual(image['status'], 'active')
        self.assertEqual(image['tags'], [])
        vgbdtg.getObject.assert_called_once_with(
            id='uuid', mask=images.IMAGE_MASK)


class TestImagesV2(unittest.TestCase):

    def setUp(self):
        self.app = mock.MagicMock()

    def test_get_v2_image_details_dict(self):
        expected_keys = [
            'status',
            'updated',
            'created',
            'id',
            'progress',
            'metadata',
            'size',
            'container_format',
            'disk_format',
            'is_public',
            'protected',
            'owner',
            'min_disk',
            'min_ram',
            'name',
            'visibility',
            'links',
            'tags',
        ]
        app, req, image, tenant_id = (mock.MagicMock(),
                                      mock.MagicMock(),
                                      mock.MagicMock(),
                                      mock.MagicMock())
        res = images.get_v2_image_details_dict(app, req, image, tenant_id)
        self.assertEqual(set(expected_keys), set(res.keys()))

    def test_get_v2_image_details_dict_fail(self):
        app, req, image, tenant_id = (mock.MagicMock(),
                                      mock.MagicMock(),
                                      None,
                                      mock.MagicMock())
        res = images.get_v2_image_details_dict(app, req, image, tenant_id)
        self.assertFalse(res)

    def _assert_image_links(self, image):
        self.assertIn('links', image)
        self.assertEqual(3, len(image['links']))
        links = (link['rel'] for link in image['links'])
        for rel in ('self', 'file', 'schema'):
            self.assertIn(rel, links)

    def test_on_get(self):
        client, env = get_client_env()
        vgbdtg = client['Virtual_Guest_Block_Device_Template_Group']
        vgbdtg.getPublicImages.return_value = [{
            'globalIdentifier': 'uuid',
            'blockDevicesDiskSpaceTotal': 1000,
            'name': 'some image',
            'status': {'keyName': 'ACTIVE', 'name': 'Active'},
        }]
        client['Account'].getPrivateBlockDeviceTemplateGroups.return_value = [{
            'globalIdentifier': 'uuid2',
            'blockDevicesDiskSpaceTotal': 2000,
            'name': 'some other image',
            'status': {'keyName': 'DEPRECATED', 'name': 'Deprecated'},
        }]

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        images.ImagesV2(self.app, detail=True).on_get(req, resp)

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['images']), 2)
        image1 = resp.body['images'][0]
        self.assertEqual(image1['id'], 'uuid')
        self.assertEqual(image1['name'], 'some image')
        self.assertEqual(image1['size'], 1000)
        self.assertEqual('active', image1['status'])
        self._assert_image_links(image1)

        image2 = resp.body['images'][1]
        self.assertEqual(image2['id'], 'uuid2')
        self.assertEqual(image2['name'], 'some other image')
        self.assertEqual(image2['size'], 2000)
        self.assertEqual('deactivated', image2['status'])
        self._assert_image_links(image2)

    def test_list_images_no_details(self):
        client, env = get_client_env()
        vgbdtg = client['Virtual_Guest_Block_Device_Template_Group']
        vgbdtg.getPublicImages.return_value = [{
            'globalIdentifier': 'uuid',
            'name': 'some image',
        }]
        client['Account'].getPrivateBlockDeviceTemplateGroups.return_value = [{
            'globalIdentifier': 'uuid2',
            'name': 'some other image',
        }]

        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        images.ImagesV2(self.app).on_get(req, resp)

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['images']), 2)
        image1 = resp.body['images'][0]
        expected_keys = ['id', 'links', 'name']
        self.assertEqual(expected_keys, sorted(image1.keys()))
        self.assertEqual(image1['id'], 'uuid')
        self.assertEqual(image1['name'], 'some image')
        self._assert_image_links(image1)

        image2 = resp.body['images'][1]
        self.assertEqual(expected_keys, sorted(image2.keys()))
        self.assertEqual(image2['id'], 'uuid2')
        self.assertEqual(image2['name'], 'some other image')
        self._assert_image_links(image2)

    def test_on_get_with_name_filter(self):
        client, env = get_client_env(query_string='name=imageA')
        vgbdtg = client['Virtual_Guest_Block_Device_Template_Group']
        vgbdtg.getPublicImages.return_value = [{
            'globalIdentifier': 'uuid',
            'blockDevicesDiskSpaceTotal': 1000,
            'name': 'imageA',
            'status': {'keyName': 'ACTIVE', 'name': 'Active'},
        }]
        client['Account'].getPrivateBlockDeviceTemplateGroups.return_value = [{
            'globalIdentifier': 'uuid2',
            'blockDevicesDiskSpaceTotal': 2000,
            'name': 'imageB',
            'status': {'keyName': 'ACTIVE', 'name': 'Active'},
        }]

        # 1. There is one image pass the filter and returned in result.
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()

        images.ImagesV2(self.app, detail=True).on_get(req, resp)

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['images']), 1)
        image1 = resp.body['images'][0]
        self.assertEqual(image1['id'], 'uuid')
        self.assertEqual(image1['name'], 'imageA')
        self.assertEqual(image1['size'], 1000)
        self.assertEqual('active', image1['status'])

        # 2. There is no any image could pass the filter and been returned.
        __client, env = get_client_env(query_string='name=imageX')
        req = api.Request(env, sl_client=__client)
        resp = falcon.Response()

        images.ImagesV2(self.app).on_get(req, resp)

        self.assertEqual(resp.status, 200)
        self.assertEqual(len(resp.body['images']), 0)
