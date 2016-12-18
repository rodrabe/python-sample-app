
import SoftLayer

from jumpgate.common import utils


class AvailabilityZonesV2(object):
    def on_get(self, req, resp, tenant_id):
        client = req.sl_client
        vs = SoftLayer.VSManager(client)

        all_options = vs.get_create_options()

        results = []
        # Load and sort all data centers
        for option in all_options['datacenters']:
            name = utils.lookup(option, 'template', 'datacenter', 'name')

            results.append({'zoneState': {'available': True}, 'hosts': None,
                            'zoneName': name})
        results = sorted(results, key=lambda x: x['zoneName'])

        resp.body = {'availabilityZoneInfo': results}
        resp.status = 200
