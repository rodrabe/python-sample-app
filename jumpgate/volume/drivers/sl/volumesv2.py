import logging
import uuid

import six

from jumpgate.common import error_handling

HTTP = six.moves.http_client  # pylint: disable=E1101
LOG = logging.getLogger(__name__)

# openstack uses uuid.uuid4() to generate UUID.
OPENSTACK_VOLUME_UUID_LEN = len(str(uuid.uuid4()))


class VolumesV2(object):
    """This code supports Iscsi network storage volumes

     On-get is used for both retrieving a list of volumes for a user and
     getting details for a specific volume
     """

    def on_get(self, req, resp, tenant_id, volume_id='detail'):
        try:
            # if the volume id is 'detail' then we will treat it as
            # a get list with detail
            if volume_id == 'detail':
                get_volume_list_detail(req, resp, tenant_id)
            else:
                get_volume(req, resp, tenant_id, volume_id)
        except Exception as e:
            error_handling.volume_fault(resp, str(e))

    def on_post(self, req, resp, tenant_id):
        resp.body = {'volume': {}}


def get_volume(req, resp, tenant_id, volume_id=None):
    LOG.debug("Retrieving information for volume with id: %s", volume_id)

    # volume id are represented by uuuid.uuid4()
    if volume_id and len(volume_id) > OPENSTACK_VOLUME_UUID_LEN:
        return error_handling.bad_request(resp,
                                          message='Volume ID is too long; '
                                          'must be less than 11 characters '
                                          'in length')
    client = req.sl_client

    iscsi = client['Network_Storage_Iscsi']
    vol = iscsi.getObject(id=volume_id, mask=get_network_storage_mask())
    LOG.debug("volume returned from softlayer: %s", vol)
    resp.body = {'volume': format_volume(tenant_id, vol)}
    resp.status = HTTP.OK
    LOG.debug("response for volume details: %s", resp.body)


def get_volume_list_detail(req, resp, tenant_id):
    LOG.debug("Retrieving volume list for user.")

    client = req.sl_client
    account = client['Account']
    iscsi_list = account.getIscsiNetworkStorage(
        mask=get_network_storage_mask())
    LOG.debug("volume list from softlayer: %s", iscsi_list[0])
    volumes = [format_volume(tenant_id,
                             vol) for vol in iscsi_list]
    LOG.debug("volume list from format: %s", volumes)
    resp.body = {'volumes': volumes}
    resp.status = HTTP.OK
    LOG.debug("response for volume list: %s", str(resp))


def format_volume(tenant_id, volume):
    def _get_volume_status(attach_cnt):

        if attach_cnt > 0:
            # The attach count is not empty. It is attached to a VSI.
            status = 'in-use'
        else:
            status = 'available'
        return status

    attachments = volume['allowedVirtualGuests']
    attachment = []
    bootable = False
    status = _get_volume_status(len(attachments))
    volume_id = volume['id']
    if volume_id is not None:
        volume_id_str = str(volume_id)
    else:
        volume_id_str = volume_id
    for blkdev in attachments:
        attachment.append(
            _translate_attachment(blkdev, volume_id))
        if blkdev.get('bootableFlag'):
            bootable = True

    zone = None
    backend_ip = None
    service_repo = volume.get('serviceResource')
    if service_repo and service_repo.get('datacenter'):
        zone = service_repo['datacenter'].get('name')
    if service_repo and service_repo.get('backendIpAddress'):
        backend_ip = service_repo.get('backendIpAddress')

    storage = None
    storage_type = volume.get('storageType')
    if storage_type and storage_type.get('description'):
        storage = storage_type['description']

    snapshot_id = None
    description = None
    owner_id = None
    updated_at = None
    tier = volume.get('storageTierLevel')
    if tier and tier.get('parentId'):
        snapshot_id = str(tier['parentId'])
    if tier and tier.get('description'):
        description = tier['description']
    if tier and tier.get('id'):
        owner_id = str(tier['id'])
    if tier and tier.get('modifyDate'):
        updated_at = tier['modifyDate']

    volinfo = {
        'id': volume_id_str,
        'name': volume.get('username'),
        'description': description,
        'size': volume.get('capacityGb'),
        'volume_type': storage,
        'metadata': {},
        'snapshot_id': snapshot_id,
        'attachments': attachment,
        'bootable': bootable,
        'availability_zone': zone,
        'created_at': volume.get('createDate'),
        'status': status,
        'migration_status': None,
        'encrypted': False,
        'os-vol-host-attr:host': backend_ip,
        'replication_status': 'disabled',
        'user_id': owner_id,
        'os-vol-tenant-attr:tenant_id': tenant_id,
        'os-vol-mig-status-attr:migstat': None,
        'multiattach': False,
        'consistencygroup_id': None,
        'updated_at': updated_at

    }

    return volinfo


def get_network_storage_mask():
    mask = [
        'id',
        'serviceResourceName',
        'createDate',
        'nasType',
        'capacityGb',
        'snapshotCapacityGb',
        'mountableFlag',
        'serviceResourceBackendIpAddress',
        'billingItem',
        'notes',
        'username',
        'password',
        'eventCount',
        'serviceResource[datacenter.name]',
        'storageType',
        'allowedVirtualGuests',
        'storageTierLevel',
        'lunId',
        'activeTransactionCount'
    ]
    return 'mask[%s]' % ','.join(mask)


def _translate_attachment(blkdev, volume_id):
    d = {}

    d['id'] = blkdev.get('id')
    d['server_id'] = blkdev.get('id')
    d['host_name'] = blkdev.get('fullyQualifiedDomainName')
    d['device'] = 'UNKNOWN'
    d['volume_id'] = volume_id
    d['attachment_id'] = blkdev.get('uuid')
    return d
