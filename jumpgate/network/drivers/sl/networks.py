import operator

from jumpgate.common import error_handling

NETWORK_MASK = 'id, name, subnets, vlanNumber, networkSpace'

VLANS = {'public': {'id': 'public',
                    'name': 'public',
                    'networkSpace': 'PUBLIC',
                    'subnets': []},
         'private': {'id': 'private',
                     'name': 'private',
                     'networkSpace': 'PRIVATE',
                     'subnets': []}}


class NetworkV2(object):
    def on_get(self, req, resp, network_id):
        """Shows information for a specified network. (net-show)

        @param req: Http Request body
        @param resp: Http Response body
        @param network_id: Network Id
        @return: Http status
        """
        client = req.sl_client
        tenant_id = req.env['auth']['tenant_id']
        if network_id in VLANS:
            vlan = VLANS[network_id]
        else:
            try:
                network_id = int(network_id)
            except Exception:
                return error_handling.bad_request(
                    resp, message="Malformed request body")

            vlan = client['Network_Vlan'].getObject(id=network_id,
                                                    mask=NETWORK_MASK)

        resp.body = {'network': format_network(vlan, tenant_id)}
        resp.status = 200


class NetworksV2(object):
    def on_get(self, req, resp):
        """Handles net-list/net-show

        @param req: Http Request body
        @param resp: Http Response body
        """
        tenant_id = req.env['auth']['tenant_id']
        client = req.sl_client

        _filter = {'networkVlans': {}}
        name_filter = req.get_param('name')
        if not name_filter:
            vlans = client['Account'].getNetworkVlans(mask=NETWORK_MASK,
                                                      filter=_filter)
            vlans += VLANS.values()
        if name_filter in VLANS:
            vlans = [VLANS[name_filter]]
        else:
            _filter['networkVlans']['id'] = {
                'operation': name_filter}
            vlans = client['Account'].getNetworkVlans(mask=NETWORK_MASK,
                                                      filter=_filter)

        network = [format_network(vlan, tenant_id)
                   for vlan in sorted(vlans, key=operator.itemgetter('id'))]

        resp.body = {'networks': network}
        resp.status = 200


def format_network(sl_vlan, tenant_id):
    return {
        'admin_state_up': True,
        'id': str(sl_vlan.get('id')),
        'name': sl_vlan.get('name'),
        'shared': False,
        'status': 'ACTIVE',
        'subnets': [str(subnet['id']) for subnet in sl_vlan['subnets']],
        'tenant_id': tenant_id,
        'provider:network_type': "vlan",
        'provider:segmentation_id': sl_vlan.get('vlanNumber'),
        'provider:physical_network': sl_vlan['networkSpace'] == 'PRIVATE',
    }
