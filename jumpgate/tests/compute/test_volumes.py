import falcon
from falcon.testing import helpers
import mock

import SoftLayer
import unittest

from jumpgate import api
from jumpgate.compute.drivers.sl import volumes

TENANT_ID = 333333
INSTANCE_ID = 7890782
VOLUME_ID = '3887490'


def get_client_env(**kwargs):
    client = mock.MagicMock()
    env = helpers.create_environ(**kwargs)
    return client, env


class TestOSVolumeAttachmentsV2(unittest.TestCase):
    def perform_attach_action(self, body_str, tenant_id, instance_id):
        self.client, self.env = get_client_env(body=body_str)
        self.req = api.Request(self.env, sl_client=self.client)
        self.resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentsV2()
        instance.on_post(self.req, self.resp, tenant_id, instance_id)

    @mock.patch('SoftLayer.VSManager.get_instance')
    @mock.patch('SoftLayer.BlockStorageManager.get_block_volume_access_list')
    @mock.patch('SoftLayer.BlockStorageManager.authorize_host_to_volume')
    def test_on_post(self, authorize_host_to_volume,
                     get_block_volume_access_list, get_instances):
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "3887490"}}')
        get_instances.return_value = {'id': INSTANCE_ID,
                                      'hostname': 'fake-server'}
        get_block_volume_access_list.return_value = {
            'allowedVirtualGuests': [],
            'id': '3887490'}
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)

        self.assertEqual(list(self.resp.body.keys()), ['volumeAttachment'])
        self.assertIn('device', self.resp.body['volumeAttachment'])
        self.assertIn('serverId', self.resp.body['volumeAttachment'])
        self.assertIn('volumeId', self.resp.body['volumeAttachment'])
        self.assertEqual(self.resp.status, 200)
        vgi = [7890782]
        authorize_host_to_volume.assert_called_once_with('3887490',
                                                         virtual_guest_ids=vgi)
        mask = 'allowedVirtualGuests[allowedHost[credential]],id'
        get_block_volume_access_list.assert_called_once_with('3887490',
                                                             mask=mask)
        get_instances.assert_called_once_with(7890782)

    @mock.patch('SoftLayer.VSManager.get_instance')
    def test_on_post_fail_empty_body(self, get_instances):
        get_instances.return_value = {'id': INSTANCE_ID,
                                      'hostname': 'fake-server'}
        body_str = '{}'
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        self.assertEqual(400, self.resp.status)

    @mock.patch('SoftLayer.VSManager.get_instance')
    def test_on_post_fail_missing_volumeAttachment(self, get_instances):
        get_instances.return_value = {'id': INSTANCE_ID,
                                      'hostname': 'fake-server'}
        body_str = '{"random_key": "random_value"}'
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        self.assertEqual(400, self.resp.status)

    @mock.patch('SoftLayer.VSManager.get_instance')
    def test_on_post_fail_missing_volumeID(self, get_instances):
        get_instances.return_value = {'id': INSTANCE_ID,
                                      'hostname': 'fake-server'}
        body_str = ('{"volumeAttachment": '
                    '{"device": null}}')
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        self.assertEqual(400, self.resp.status)

    @mock.patch('SoftLayer.VSManager.get_instance')
    def test_on_post_fail_instance_id_not_number(self, get_instances):
        get_instances.return_value = {'id': INSTANCE_ID,
                                      'hostname': 'fake-server'}
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "388749A"}}')

        self.perform_attach_action(body_str, TENANT_ID, 'not a number')
        resp_body = {'notFound': {'message': 'Invalid instance ID specified.',
                                  'code': '404'}}
        self.assertEqual(resp_body, self.resp.body)

    @mock.patch('SoftLayer.VSManager.get_instance')
    @mock.patch('SoftLayer.BlockStorageManager.get_block_volume_access_list')
    def test_on_post_fail_volume_already_attach(self,
                                                get_block_volume_access_list,
                                                get_instances):
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "3887490"}}')
        get_instances.return_value = {'id': INSTANCE_ID,
                                      'hostname': 'fake-server'}
        get_block_volume_access_list.return_value = {
            'allowedVirtualGuests': [{
                'name': 'iqn.2005-05.com.softlayer:SL01SU720429-V24684417'}],
            'id': '3887490'}
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)

        resp_body = {'volumeFault': {'message': 'The requested volume is'
                                                ' already attached to a '
                                                'guest.',
                                     'code': '400'}}
        self.assertEqual(resp_body, self.resp.body)

        mask = 'allowedVirtualGuests[allowedHost[credential]],id'
        get_block_volume_access_list.assert_called_once_with('3887490',
                                                             mask=mask)
        get_instances.assert_called_once_with(7890782)

    @mock.patch('SoftLayer.VSManager.get_instance')
    @mock.patch('SoftLayer.BlockStorageManager.get_block_volume_access_list')
    def test_on_post_fail_vb_client_no_volume(self,
                                              get_block_volume_access_list,
                                              get_instances):
        get_instances.return_value = {'id': '1111111',
                                      'hostname': 'fake-server'}
        get_block_volume_access_list.return_value = {
            'allowedVirtualGuests': [{
                'name': 'iqn.2005-05.com.softlayer:SL01SU720429-V24684417'}],
            'id': '3887490'}
        get_block_volume_access_list.side_effect = Exception('badrequest')
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "3887490"}}')
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        resp_body = {'volumeFault': {'message': 'The requested volume was '
                                                'not found',
                                     'code': '404'}}
        self.assertEqual(resp_body, self.resp.body)
        mask = 'allowedVirtualGuests[allowedHost[credential]],id'
        get_block_volume_access_list.assert_called_once_with('3887490',
                                                             mask=mask)
        get_instances.assert_called_once_with(7890782)

    @mock.patch('SoftLayer.VSManager.get_instance')
    def test_on_post_fail_vb_client_no_instance(self,

                                                get_instances):
        get_instances.side_effect = Exception('badrequest')
        get_instances.return_value = {'id': '1111111',
                                      'hostname': 'fake-server'}
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "3887490"}}')
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        resp_body = {'volumeFault': {'message': 'The requested instance was '
                                                'not found',
                                     'code': '404'}}
        self.assertEqual(resp_body, self.resp.body)
        get_instances.assert_called_once_with(7890782)

    @mock.patch('SoftLayer.VSManager.get_instance')
    def test_on_post_fail_vs_client_no_instance(self,
                                                get_instances):
        get_instances.side_effect = Exception('badrequest')
        get_instances.return_value = {'id': '1111111',
                                      'hostname': 'fake-server'}
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "3887490"}}')
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        resp_body = {'volumeFault': {'message': 'The requested instance was '
                                                'not found',
                                     'code': '404'}}
        self.assertEqual(resp_body, self.resp.body)
        get_instances.assert_called_once_with(7890782)

    @mock.patch('SoftLayer.VSManager.get_instance')
    @mock.patch('SoftLayer.BlockStorageManager.get_block_volume_access_list')
    @mock.patch('SoftLayer.BlockStorageManager.authorize_host_to_volume')
    def test_on_post_fail_vb_client_attach(self,
                                           authorize_host_to_volume,
                                           get_block_volume_access_list,
                                           get_instances):
        authorize_host_to_volume.side_effect = Exception('Exception Received')
        get_instances.return_value = {'id': '1111111',
                                      'hostname': 'fake-server'}
        get_block_volume_access_list.return_value = {
            'allowedVirtualGuests': [],
            'id': '3887490'}
        body_str = ('{"volumeAttachment": '
                    '{"device": null, "volumeId": "3887490"}}')
        self.perform_attach_action(body_str, TENANT_ID, INSTANCE_ID)
        resp_body = {'volumeFault': {'message': 'Exception Received',
                                     'code': '400'}}
        self.assertEqual(resp_body, self.resp.body)

        vgi = [7890782]
        authorize_host_to_volume.assert_called_once_with('3887490',
                                                         virtual_guest_ids=vgi)
        mask = 'allowedVirtualGuests[allowedHost[credential]],id'
        get_block_volume_access_list.assert_called_once_with('3887490',
                                                             mask=mask)
        get_instances.assert_called_once_with(7890782)

    def perform_volume_list(self, tenant_id, instance_id):
        self.client, self.env = get_client_env()
        self.vg_clientMock = self.client['Virtual_Guest']
        self.vdi_clientMock = self.client['Virtual_Disk_Image']
        self.req = api.Request(self.env, sl_client=self.client)
        self.resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentsV2()
        instance.on_get(self.req, self.resp, tenant_id, instance_id)

    def test_on_get(self):
        self.client, self.env = get_client_env()
        self.vg_clientMock = self.client['Virtual_Guest']
        self.vg_clientMock.getBlockDevices.return_value = [{'diskImage':
                                                            {'type':
                                                             {'keyName':
                                                              'not SWAP'},
                                                             'id': '0123456'}
                                                            }]
        self.vdi_clientMock = self.client['Virtual_Disk_Image']
        self.req = api.Request(self.env, sl_client=self.client)
        self.resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentsV2()
        instance.on_get(self.req, self.resp, TENANT_ID, INSTANCE_ID)
        self.assertEqual(list(self.resp.body.keys()), ['volumeAttachments'])
        self.assertIn('device', self.resp.body['volumeAttachments'][0])
        self.assertIn('id', self.resp.body['volumeAttachments'][0])
        self.assertIn('serverId', self.resp.body['volumeAttachments'][0])
        self.assertIn('volumeId', self.resp.body['volumeAttachments'][0])

    def test_on_get_fail_instance_id_not_a_number(self):
        self.perform_volume_list(TENANT_ID, 'not a number')
        self.assertEqual(self.resp.body, {'notFound':
                                          {'message':
                                           'Invalid instance ID specified.',
                                           'code': '404'}})

    def test_on_get_fail_block_devices_exception(self):
        client, env = get_client_env()
        vg_clientMock = client['Virtual_Guest']
        gbdMock = vg_clientMock.getBlockDevices
        gbdMock.side_effect = SoftLayer.SoftLayerAPIError(404,
                                                          'No Block Devices',
                                                          None)
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentsV2()
        instance.on_get(req, resp, TENANT_ID, INSTANCE_ID)
        self.assertEqual(resp.body, {'volumeFault':
                                     {'message': 'No Block Devices',
                                      'code': '500'}})


class TestOSVolumeAttachmentV2(unittest.TestCase):
    def perform_detach_action(self, tenant_id, instance_id, volume_id):
        self.client, self.env = get_client_env()
        self.vg_clientMock = self.client['Virtual_Guest']
        self.vdi_clientMock = self.client['Virtual_Disk_Image']
        self.req = api.Request(self.env, sl_client=self.client)
        self.resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_delete(self.req, self.resp, tenant_id,
                           instance_id, volume_id)

    def test_on_delete(self):
        client, env = get_client_env()
        vg_clientMock = client['Virtual_Guest']
        vdi_clientMock = client['Virtual_Disk_Image']
        vdi_clientMock.getObject.return_value = {'blockDevices':
                                                 [{'guestId': INSTANCE_ID}]}
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_delete(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        vg_clientMock.detachDiskImage.assert_called_with(VOLUME_ID,
                                                         id=INSTANCE_ID)
        self.assertEqual(resp.status, 202)

    def test_on_delete_fail_instance_id_not_a_number(self):
        self.perform_detach_action(TENANT_ID, 'not a number', VOLUME_ID)
        self.assertEqual(self.resp.body, {'notFound': {'message':
                                                       'Invalid instance'
                                                       ' ID specified.',
                                                       'code': '404'}})

    def test_on_delete_fail_volume_id_too_long(self):
        self.perform_detach_action(TENANT_ID, INSTANCE_ID,
                                   '0123456789012345678901234567890123456789')
        self.assertEqual(self.resp.body, {'badRequest':
                                          {'message': 'Malformed request '
                                           'body', 'code': '400'}})

    def test_on_delete_fail_detach_exception(self):
        client, env = get_client_env()
        vg_clientMock = client['Virtual_Guest']
        deiMock = vg_clientMock.detachDiskImage
        deiMock.side_effect = (SoftLayer.SoftLayerAPIError(404,
                                                           'Detach Error',
                                                           None))
        vdi_clientMock = client['Virtual_Disk_Image']
        vdi_clientMock.getObject.return_value = {'blockDevices':
                                                 [{'guestId': INSTANCE_ID}]}
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_delete(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        vg_clientMock.detachDiskImage.assert_called_with(VOLUME_ID,
                                                         id=INSTANCE_ID)
        self.assertEqual(resp.body, {'volumeFault':
                                     {'message': 'Detach Error',
                                      'code': '500'}})

    def test_on_delete_fail_detach_getObject_exception(self):
        client, env = get_client_env()
        vdi_clientMock = client['Virtual_Disk_Image']
        vdi_clientMock.getObject.side_effect = (SoftLayer.
                                                SoftLayerAPIError(404,
                                                                  'No Object',
                                                                  None))
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_delete(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        vdi_clientMock.getObject.assert_called_with(id=VOLUME_ID,
                                                    mask='blockDevices')
        self.assertEqual(resp.body, {'volumeFault':
                                     {'message': 'No Object',
                                      'code': '500'}})

    def test_on_delete_fail_disk_already_attached(self):
        client, env = get_client_env()
        vdi_clientMock = client['Virtual_Disk_Image']
        vdi_clientMock.getObject.return_value = {'blockDevices':
                                                 [{'guestId': '0123456'}]}
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_delete(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        self.assertEqual(resp.body, {'volumeFault':
                                     {'message': 'The requested disk image '
                                      'is attached to another guest and '
                                      'cannot be detached.',
                                      'code': '400'}})

    def perform_get_vol_details(self, tenant_id, instance_id, volume_id):
        self.client, self.env = get_client_env()
        self.vg_clientMock = self.client['Virtual_Guest']
        self.vdi_clientMock = self.client['Virtual_Disk_Image']
        self.req = api.Request(self.env, sl_client=self.client)
        self.resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_get(self.req, self.resp, tenant_id,
                        instance_id, volume_id)

    def test_on_get(self):
        client, env = get_client_env()
        vg_clientMock = client['Virtual_Guest']
        vg_clientMock.getBlockDevices.return_value = [{'diskImage':
                                                       {'type':
                                                        {'keyName':
                                                         'not SWAP'},
                                                        'id': VOLUME_ID}}]
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_get(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        self.assertEqual(list(resp.body.keys()), ['volumeAttachment'])
        self.assertIn('device', resp.body['volumeAttachment'])
        self.assertIn('id', resp.body['volumeAttachment'])
        self.assertIn('serverId', resp.body['volumeAttachment'])
        self.assertIn('volumeId', resp.body['volumeAttachment'])

    def test_on_get_fail_instance_id_not_a_number(self):
        self.perform_get_vol_details(TENANT_ID, 'not a number', VOLUME_ID)
        self.assertEqual(self.resp.body, {'notFound':
                                          {'message': 'Invalid instance ID '
                                                      'specified.',
                                           'code': '404'}})

    def test_on_get_fail_volume_id_too_long(self):
        self.perform_get_vol_details(TENANT_ID, INSTANCE_ID,
                                     '0123456789012345678901234567890123456')
        self.assertEqual(self.resp.body,
                         {'badRequest': {'message': 'Malformed request '
                                         'body', 'code': '400'}})

    def test_on_get_fail_invalid_volume_id(self):
        client, env = get_client_env()
        vg_clientMock = client['Virtual_Guest']
        vg_clientMock.getBlockDevices.return_value = [{'diskImage':
                                                       {'type':
                                                        {'keyName':
                                                         'not SWAP'},
                                                        'id': '0123456'}}]
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_get(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        self.assertEqual(resp.body, {'volumeFault':
                                     {'message': 'Invalid volume id.',
                                      'code': '400'}})

    def test_on_get_no_block_devices(self):
        client, env = get_client_env()
        vg_clientMock = client['Virtual_Guest']
        gbdMock = vg_clientMock.getBlockDevices
        gbdMock.side_effect = SoftLayer.SoftLayerAPIError(404,
                                                          'No Block Devices',
                                                          None)
        req = api.Request(env, sl_client=client)
        resp = falcon.Response()
        instance = volumes.OSVolumeAttachmentV2()
        instance.on_get(req, resp, TENANT_ID, INSTANCE_ID, VOLUME_ID)
        self.assertEqual(resp.body, {'volumeFault':
                                     {'message': 'No Block Devices',
                                      'code': '500'}})
