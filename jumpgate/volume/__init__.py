

def add_endpoints(disp):
    # V2 API - http://api.openstack.org/api-ref-blockstorage.html#volumes-api

    disp.add_endpoint('index', '/')

    disp.add_endpoint('v2_detail', '/v2')
    disp.add_endpoint('v2_volumes', '/v2/{tenant_id}/volumes')
    disp.add_endpoint('v2_os_volumes', '/v2/{tenant_id}/os-volumes')

    disp.add_endpoint('v2_volumes_detail', '/v2/{tenant_id}/volumes/detail')
    disp.add_endpoint('v2_volume', '/v2/{tenant_id}/volumes/{volume_id}')
    disp.add_endpoint('v2_volume_types', '/v2/{tenant_id}/types')
    disp.add_endpoint('v2_volume_type',
                      '/v2/{tenant_id}/types/{type_id}')
    disp.add_endpoint('v2_snapshots', '/v2/{tenant_id}/snapshots')
    disp.add_endpoint('v2_snapshot', '/v2/{tenant_id}/snapshots/{snapshot_id}')

    # V1 API - Unknown link
    # TODO(mriedem): Remove the v1 API. The compute volume proxy will need
    # to use the v2 volume API and translate any values as necessary.

    disp.add_endpoint('v1_snapshots_detail',
                      '/v1/{tenant_id}/snapshots/detail')
    disp.add_endpoint('v1_volume_types', '/v1/{tenant_id}/types')
    disp.add_endpoint('v1_volumes', '/v1/{tenant_id}/volumes')
    disp.add_endpoint('v1_volume', '/v1/{tenant_id}/volumes/{volume_id}')
    disp.add_endpoint('v1_volumes_detail', '/v1/{tenant_id}/volumes/detail')
