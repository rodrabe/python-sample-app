from mock import MagicMock
from mock import patch
import unittest

from jumpgate.compute.drivers.sl.availability_zones import (
    AvailabilityZonesV2)


class TestAvailabilityZonesV2(unittest.TestCase):

    def setUp(self):
        self.req, self.resp = MagicMock(), MagicMock()
        self.tenant_id = '1234'
        self.instance = AvailabilityZonesV2()

    @patch('SoftLayer.VSManager.get_create_options')
    def test_on_get(self, mockOptions):
        mockOptions.return_value = {
            'datacenters':
            [{'template': {'datacenter': {'name': 'dal01'}}},
             {'template': {'datacenter': {'name': 'ams01'}}},
             {'template': {'datacenter': {'name': 'sng01'}}}]}
        self.instance.on_get(self.req, self.resp, self.tenant_id)
        self.assertEqual(list(self.resp.body.keys()),
                         ['availabilityZoneInfo'])
        self.assertEqual(self.resp.body['availabilityZoneInfo'],
                         [{'zoneState': {'available': True},
                           'hosts': None, 'zoneName': 'ams01'},
                          {'zoneState': {'available': True},
                           'hosts': None, 'zoneName': 'dal01'},
                          {'zoneState': {'available': True},
                           'hosts': None, 'zoneName': 'sng01'}])
        self.assertEqual(self.resp.status, 200)

    def tearDown(self):
        self.req, self.resp, self.app = None, None, None
