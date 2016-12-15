import unittest

import falcon
from falcon.testing import helpers
import mock

from jumpgate import api
from jumpgate.volume.drivers.sl import volumesv2
import SoftLayer

TENANT_ID = 333333
GUEST_ID = 111111
DISK_IMG_ID = 222222
BLKDEV_MOUNT_ID = '0'
GOOD_VOLUME_ID = '100000'
"""Invalid volume id (way too long of a volume id) used for details lookup"""
INVALID_VOLUME_ID = 'ABCDEFGDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD'

OP_CODE = {
    'GOOD_PATH': {
        'SIMPLE': 1,
        'RET_VOLUMES': 4,
        'RET_VOLUME': 5,

    },
    'BAD_PATH': {
        'VOLUME_INVALID': 2,
        'GET_VOLUMES_API': 3,

    }
}

test_volume = {"migration_status": None, "attachments": [],
               "availability_zone": "lon02",
               "os-vol-host-attr:host": "nfslon0202c-fz.service.softlayer.com",
               "encrypted": False, "updated_at": "2016-11-02T08:47:30-06:00",
               "replication_status": "disabled", "snapshot_id": "133116391",
               "id": "15776357", "size": 40, "user_id": "133116401",
               "os-vol-tenant-attr:tenant_id": "720429",
               "os-vol-mig-status-attr:migstat": None, "metadata": {},
               "status": "available", "description": "2 IOPS per GB",
               "multiattach": False, "consistencygroup_id": None,
               "name": "SL01SEL720429-10", "bootable": False,
               "created_at": "2016-11-01T07:57:53-06:00",
               "volume_type": "Endurance Block Storage"}


def _set_up_req_resp():
    env = helpers.create_environ()
    req = falcon.Request(env)
    resp = falcon.Response()
    client = mock.MagicMock()
    req = api.Request(env, sl_client=client)
    return req, resp


class TestVolumeV2(unittest.TestCase):
    """Unit tests for class VolumeV2"""

    def setUp(self):
        self.req, self.resp = _set_up_req_resp()
        self.rsc = volumesv2.VolumesV2()

    def test_on_get_for_volume_details_good(self):
        """Test the good path of show volume"""
        self.rsc.on_get(self.req, self.resp, TENANT_ID, GOOD_VOLUME_ID)
        self.assertEqual(200, self.resp.status)
        volume = self.resp.body['volume']
        self.assertEqual(['volume'], list(self.resp.body.keys()))
        volume = self.resp.body['volume']
        self.assertItemsEqual(volume.keys(),
                              test_volume.keys())

    def test_on_get_for_volume_details_invalid_volume_id(self):
        """Test the bad path of show volume with invalid volume id"""
        self.rsc.on_get(self.req, self.resp, TENANT_ID, INVALID_VOLUME_ID)
        self.assertEqual(400, self.resp.status)

    def test_on_get_for_volume_details_SoftLayerAPIError(self):
        """Test the bad path of show volume"""
        set_SL_client(
            self.req,
            operation=OP_CODE['BAD_PATH']['GET_VOLUMES_API'])
        self.rsc.on_get(self.req, self.resp, TENANT_ID, 'detail')
        self.assertEqual(500, self.resp.status)

    def test_on_get_for_volume_details_good_format_volumes(self):
        """Test the good path of format_volume func during show volume"""
        set_SL_client(
            self.req,
            operation=OP_CODE['GOOD_PATH']['RET_VOLUMES'])
        self.rsc.on_get(self.req, self.resp, TENANT_ID, 'detail')
        self.assertEqual(200, self.resp.status)
        self.assertEqual(['volumes'], list(self.resp.body.keys()))
        volume = self.resp.body['volumes'][0]
        self.assertItemsEqual(set(volume.keys()),
                              set(test_volume.keys()))


def set_SL_client(req, operation=OP_CODE['GOOD_PATH']['SIMPLE']):
    if operation == OP_CODE['BAD_PATH']['VOLUME_INVALID']:
        # Network_Storage_Iscsi.getObject failure.
        req.sl_client[
            'Network_Storage_Iscsi'].getObject = mock.MagicMock(

            side_effect=SoftLayer.SoftLayerAPIError(400,
                                                    'MockFault',
                                                    None))
    elif operation == OP_CODE['BAD_PATH']['GET_VOLUMES_API']:
        # getIscsiNetworkStorage() SLAPI failure
        req.sl_client[
            'Account'].getIscsiNetworkStorage = mock.MagicMock(
            side_effect=SoftLayer.SoftLayerAPIError(400,
                                                    'MockFault',
                                                    None))
    elif operation == OP_CODE['GOOD_PATH']['RET_VOLUMES']:

        def _return_disk_imgs(*args, **kwargs):
            return [{'username': 'SL01SEL720429-1', 'capacityGb': 20,
                     'nasType': 'ISCSI', 'eventCount': 1,
                     'mountableFlag': '1',
                     'createDate': '2016-10-04T14:04:51-06:00',
                     'serviceResourceName': 'PerfStor  aggr_staastor0101_pc01',
                     'storageTierLevel': {
                         'modifyDate': '2016-10-15T23:09:56-06:00',
                         'recurringMonths': 1,
                         'id': 129688103, 'setupFee': '0', 'recurringFee': '0',
                         'lastBillDate': '2016-10-15T23:09:56-06:00',
                         'nextBillDate': '2016-11-16T00:00:00-06:00',
                         'createDate': '2016-10-04T14:04:28-06:00',
                         'oneTimeFeeTaxRate': '0',
                         'laborFeeTaxRate': '0', 'parentId': 129688099,
                         'cancellationDate': '',
                         'cycleStartDate': '2016-10-15T23:09:56-06:00',
                         'description': '0.25 IOPS per GB', 'laborFee': '0',
                         'oneTimeFee': '0',
                         'setupFeeTaxRate': '0',
                         'categoryCode': 'storage_tier_level',
                         'allowCancellationFlag': 1,
                         'associatedBillingItemId': '129688099',
                         'serviceProviderId': 1, 'orderItemId': 155795847,
                         'recurringFeeTaxRate': '0'},
                     'activeTransactionCount': 0,
                     'allowedVirtualGuests': [
                         {'domain': 'softlayer.com',
                          'modifyDate': '2016-10-04T13:53:47-06:00',
                          'dedicatedAccountHostOnlyFlag': False, 'maxCpu': 1,
                          'maxMemory': 2048,
                          'primaryIpAddress': '169.53.180.102',
                          'globalIdentifier': '036f071d-a86a-4fe-00d10f9a1742',
                          'maxCpuUnits': 'CORE', 'id': 24684417,
                          'accountId': 720429,
                          'uuid': 'dff0521b-d17a-bf1c-1eb7-4f0229b911b8',
                          'metricPollDate': '',
                          'createDate': '2016-10-04T13:51:30-06:00',
                          'hostname': 'harvesters-test',
                          'lastVerifiedDate': '',
                          'primaryBackendIpAddress': '10.115.32.11',
                          'lastPowerStateId': '',
                          'status': {'keyName': 'ACTIVE', 'name': 'Active'},
                          'fullyQualifiedDomainName': 'harvesters-ftlayer.com',
                          'provisionDate': '2016-10-04T13:53:47-06:00',
                          'startCpus': 1, 'statusId': 1001}],
                     'serviceResourceBackendIpAddress': '10.2.62.90',
                     'storageType': {'keyName': 'ENDURANCE_BLOCK_STORAGE',
                                     'description': 'Endurance Block Storage',
                                     'id': 7}, 'snapshotCapacityGb': '5',
                     'billingItem': {'modifyDate': '2016-10-15T23:09:56-06:00',
                                     'recurringMonths': 1,
                                     'id': 129688099,
                                     'setupFee': '0', 'recurringFee': '0',
                                     'lastBillDate': '2016-10-T23:09:56-06:00',
                                     'nextBillDate': '2016-11-T00:00:00-06:00',
                                     'createDate': '2016-10-04T14:04:28-06:00',
                                     'oneTimeFeeTaxRate': '0',
                                     'laborFeeTaxRate': '0', 'parentId': '',
                                     'cancellationDate': '',
                                     'cycleStartDate': '2016-1023:09:56-06:00',
                                     'description': 'Endurance Storage',
                                     'laborFee': '0', 'oneTimeFee': '0',
                                     'setupFeeTaxRate': '0',
                                     'categoryCode': 'storage_vice_enterprise',
                                     'allowCancellationFlag': 1,
                                     'serviceProviderId': 1,
                                     'orderItemId': 155795843,
                                     'recurringFeeTaxRate': '0'},
                     'serviceResource': {'datacenter': {'name': 'tor01'},
                                         'backendIpAddress': 'nfstor0101b.com',
                                         'name': 'PerfStor Aggrastor0101_pc01',
                                         'id': 2402},
                     'lunId': '170',
                     'id': 14912989},
                    {'username': 'SL01SL720429-1', 'capacityGb': 1000,
                     'nasType': 'ISCSI', 'eventCount': 1,
                     'mountableFlag': '1',
                     'createDate': '2015-11-18T12:33:22-06:00',
                     'serviceResourceName': 'PerfStor Aggr agtaasdal0501_hp01',
                     'serviceResourceBackendIpAddress': '10.1.154.64',
                     'activeTransactionCount': 0,
                     'allowedVirtualGuests': [], 'iops': '3000',
                     'storageType': {'keyName': 'PERFORMANCE_BLOCK_STORAGE',
                                     'description': 'Performance Block Storge',
                                     'id': 5},
                     'billingItem': {'modifyDate': '2016-10-15T23:09:56-06:00',
                                     'recurringMonths': 1,
                                     'id': 75367811,
                                     'setupFee': '0', 'recurringFee': '0',
                                     'lastBillDate': '2016-10-15T23:096-06:00',
                                     'nextBillDate': '2016-11-16T00::00-06:00',
                                     'createDate': '2015-11-18T12:32:59-06:00',
                                     'oneTimeFeeTaxRate': '0',
                                     'laborFeeTaxRate': '0', 'parentId': '',
                                     'cancellationDate': '',
                                     'cycleStartDate': '2016-10-15T3:56-06:00',
                                     'description': 'Block Storage rformance)',
                                     'laborFee': '0',
                                     'oneTimeFee': '0',
                                     'setupFeeTaxRate': '0',
                                     'categoryCode': 'performance_torae_iscsi',
                                     'allowCancellationFlag': 1,
                                     'serviceProviderId': 1,
                                     'orderItemId': 97797309,
                                     'recurringFeeTaxRate': '0'},
                     'serviceResource': {'datacenter': {'name': 'dal05'},
                                         'backendIpAddress': 'nfsdatlayer.com',
                                         'name': 'PerfStor Aggr agsl0501_hp01',
                                         'id': 2218}, 'lunId': '170',
                     'id': 7382015}]

        req.sl_client['Account'].getIscsiNetworkStorage = mock.MagicMock(
            side_effect=_return_disk_imgs)
    elif operation == OP_CODE['GOOD_PATH']['RET_VOLUME']:
        def _return_volume():
            a = [{'username': 'SL01SEL720429-1', 'capacityGb': '20',
                  'nasType': 'ISCSI', 'eventCount': 1,
                  'mountableFlag': '1',
                  'createDate': '2016-10-04T14:04:51-06:00',
                  'serviceResourceName': 'PerfStor Aggr aggr_staastr0101_pc01',
                  'storageTierLevel': {
                      'modifyDate': '2016-10-15T23:09:56-06:00',
                      'recurringMonths': 1,
                      'id': '129688103', 'setupFee': '0',
                      'recurringFee': '0',
                      'lastBillDate': '2016-10-15T23:09:56-06:00',
                      'nextBillDate': '2016-11-16T00:00:00-06:00',
                      'createDate': '2016-10-04T14:04:28-06:00',
                      'oneTimeFeeTaxRate': '0',
                      'laborFeeTaxRate': '0', 'parentId': '129688099',
                      'cancellationDate': '',
                      'cycleStartDate': '2016-10-15T23:09:56-06:00',
                      'description': '0.25 IOPS per GB', 'laborFee': '0',
                      'oneTimeFee': '0',
                      'setupFeeTaxRate': '0',
                      'categoryCode': 'storage_tier_level',
                      'allowCancellationFlag': '1',
                      'associatedBillingItemId': '129688099',
                      'serviceProviderId': '1', 'orderItemId': '155795847',
                      'recurringFeeTaxRate': '0'},
                  'activeTransactionCount': '0',
                  'allowedVirtualGuests': [
                      {'domain': 'softlayer.com',
                       'modifyDate': '2016-10-04T13:53:47-06:00',
                       'dedicatedAccountHostOnlyFlag': 'False',
                       'maxCpu': '1',
                       'maxMemory': '2048',
                       'primaryIpAddress': '169.53.180.102',
                       'globalIdentifier': '036f071d-a86a-4922-92fe-00f9a1742',
                       'maxCpuUnits': 'CORE', 'id': '24684417',
                       'accountId': '720429',
                       'uuid': 'dff0521b-d17a-bf1c-1eb7-4f0229b911b8',
                       'metricPollDate': '',
                       'createDate': '2016-10-04T13:51:30-06:00',
                       'hostname': 'harvesters-test',
                       'lastVerifiedDate': '',
                       'primaryBackendIpAddress': '10.115.32.11',
                       'lastPowerStateId': '',
                       'status': {'keyName': 'ACTIVE', 'name': 'Active'},
                       'fullyQualifiedDomainName': 'harvesters-tsoftlayer.com',
                       'provisionDate': '2016-10-04T13:53:47-06:00',
                       'startCpus': '1',
                       'statusId': '1001'}],
                  'serviceResourceBackendIpAddress': '10.2.62.75',
                  'storageType': {'keyName': 'ENDURANCE_BLOCK_STORAGE',
                                  'description': 'Endurance Block Storage',
                                  'id': '7'}, 'snapshotCapacityGb': '5',
                  'billingItem': {'modifyDate': '2016-10-15T23:09:56-06:00',
                                  'recurringMonths': '1',
                                  'id': '129688099',
                                  'setupFee': '0', 'recurringFee': '0',
                                  'lastBillDate': '2016-10-15T23:09:56-06:00',
                                  'nextBillDate': '2016-11-16T00:00:00-06:00',
                                  'createDate': '2016-10-04T14:04:28-06:00',
                                  'oneTimeFeeTaxRate': '0',
                                  'laborFeeTaxRate': '0', 'parentId': '',
                                  'cancellationDate': '',
                                  'cycleStartDate': '2016-10-15T2:09:56-06:00',
                                  'description': 'Endurance Storage',
                                  'laborFee': '0', 'oneTimeFee': '0',
                                  'setupFeeTaxRate': '0',
                                  'categoryCode': 'storage_service_enterprise',
                                  'allowCancellationFlag': '1',
                                  'serviceProviderId': '1',
                                  'orderItemId': '155795843',
                                  'recurringFeeTaxRate': '0'},
                  'serviceResource': {'datacenter': {'name': 'tor01'},
                                      'backendIpAddress': 'nfstosoftlayer.com',
                                      'name': 'PerfStor Aggr aggstor0101_pc01',
                                      'id': '2402'},
                  'lunId': '170',
                  'id': '14912989'}]
            return a

        req.sl_client[
            'Network_Storage_Iscsi'].getObject = mock.MagicMock(
            side_effect=_return_volume())
