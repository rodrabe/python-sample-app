import json
import logging
import uuid

import jsonschema

import six
import SoftLayer

from jumpgate.common import error_handling

LOG = logging.getLogger(__name__)

HTTP = six.moves.http_client  # pylint: disable=E1101

# openstack is use uuid.uuid4() to generate UUID.
OPENSTACK_VOLUME_UUID_LEN = len(str(uuid.uuid4()))

CREATE_VOLUME_ATTACHMENT_SCHEMA = {
    'type': 'object',
    'properties': {
        'volumeAttachment': {
            'type': 'object',
            'properties': {
                'volumeId': {'type': 'string', 'format': 'uuid'},
                'device': {
                    'type': ['string', 'null'],
                    # NOTE: The validation pattern from match_device() in
                    #       nova/block_device.py.
                    'pattern': '(^/dev/x{0,1}[a-z]{0,1}d{0,1})([a-z]+)[0-9]*$'
                }
            },
            'required': ['volumeId'],
            'additionalProperties': False,
        },
    },
    'required': ['volumeAttachment'],
    'additionalProperties': False,
}

CREATE_VOLUME_ATTACHMENT_VALIDATOR = jsonschema.Draft4Validator(
    CREATE_VOLUME_ATTACHMENT_SCHEMA)


class OSVolumeAttachmentsV2(object):
    """class OSVolumeAttachmentsV2 supports the following nova volume endpoints

    GET /v2/{tenant_id}/servers/{server_id}/os-volume_attachments
        -- Lists the volume attachments for a specified server.
    POST /v2/{tenant_id}/servers/{server_id}/os-volume_attachments
        -- Attaches a specified volume to a specified server.
    """

    def on_get(self, req, resp, tenant_id, instance_id):
        '''Lists volume attachments for the instance.'''
        vg_client = req.sl_client['Virtual_Guest']
        try:
            instance_id = int(instance_id)
        except Exception:
            return error_handling.not_found(resp,
                                            "Invalid instance ID specified.")

        try:
            blkDevices = vg_client.getBlockDevices(mask='id, diskImage.type',
                                                   id=instance_id)

            vols = [format_volume_attachment(vol['diskImage']['id'],
                                             instance_id,
                                             '')
                    for vol in blkDevices
                    if vol['diskImage']['type']['keyName'] != 'SWAP']
            resp.body = {"volumeAttachments": vols}
        except Exception as e:
            error_handling.volume_fault(resp, e.faultString)

    def on_post(self, req, resp, tenant_id, instance_id):
        '''Attaches a specified volume to a specified server.'''
        vs_mgr = SoftLayer.VSManager(req.sl_client)

        try:
            instance_id = int(instance_id)
        except Exception:
            # If the instance ID is not valid an exception will be sent
            return error_handling.not_found(resp,
                                            "Invalid instance ID specified.")
        # Get the instance to verify it exists;  also using info from
        # instance to fill out the response object
        try:
            instance = vs_mgr.get_instance(instance_id)
        except Exception as e:
            # If the instance is not found an exception will be sent
            return error_handling.volume_fault(
                resp,
                'The requested instance was not found',
                code=HTTP.NOT_FOUND)

        if not instance:
            return error_handling.volume_fault(
                resp,
                'The requested instance was not found',
                code=HTTP.NOT_FOUND)

        # Get the volume ID from the request body
        body = json.loads(req.stream.read().decode())

        CREATE_VOLUME_ATTACHMENT_VALIDATOR.validate(body)

        volume_id = body['volumeAttachment']['volumeId']

        # first let's check if the volume is already attached
        block_mgr = SoftLayer.BlockStorageManager(req.sl_client)
        blk_devices = []

        try:
            # get the volume info to see if there are any attachments
            # it also verifies that the volume exists

            items = {
                'id',
                'allowedVirtualGuests[allowedHost[credential]]'
            }
            al_mask = ','.join(items)
            access_list = block_mgr.get_block_volume_access_list(volume_id,
                                                                 mask=al_mask)
            blk_devices = access_list['allowedVirtualGuests']

        except Exception as e:
            return error_handling.volume_fault(
                resp,
                'The requested volume was not found',
                code=HTTP.NOT_FOUND)

        if len(blk_devices) > 0:
            return error_handling.volume_fault(
                resp,
                'The requested volume is already attached to '
                'a guest.',
                code=HTTP.BAD_REQUEST)

        try:

            # attach the volume;  authorizing the host to the volume
            block_mgr.authorize_host_to_volume(volume_id,
                                               virtual_guest_ids=[instance_id])
            volume_att = {'device': "",
                          'serverId': instance_id,
                          'volumeId': volume_id}
            resp.body = {"volumeAttachment": volume_att}

            resp.status = HTTP.OK

        except Exception as e:
            return error_handling.volume_fault(resp,
                                               message=str(e),
                                               code=HTTP.BAD_REQUEST)


class OSVolumeAttachmentV2(object):
    """class OSVolumeAttachmentsV2 supports the following nova volume endpoints

    GET /v2/{tenant_id}/servers/{server_id}/os-volume_attachments/
    {attachment_id} -- Shows details for the specified volume attachment.

    DELETE /v2/{tenant_id}/servers/{server_id}/os-volume_attachments/
    {attachment_id}
        -- Detaches a specified volume attachment from a specified server.
    """
    def on_get(self, req, resp, tenant_id, instance_id, volume_id):
        '''Shows details for the specified volume attachment.'''
        try:
            instance_id = int(instance_id)
        except Exception:
            return error_handling.not_found(resp,
                                            "Invalid instance ID specified.")

        if volume_id and len(volume_id) > OPENSTACK_VOLUME_UUID_LEN:
            return error_handling.bad_request(resp,
                                              message="Malformed request body")

        # since detail has the same info as the input request params, we can
        # just return the values back in the response using the request params.
        # But instead we will do sanity check to ensure the volume_id belongs
        # to the instance.
        vg_client = req.sl_client['Virtual_Guest']
        try:
            blkDevices = vg_client.getBlockDevices(mask='id, diskImage.type',
                                                   id=instance_id)
            vols = [x for x in blkDevices
                    if x['diskImage']['type']['keyName'] != 'SWAP']
            for vol in vols:
                json_response = None
                vol_disk_id = vol['diskImage']['id']
                if str(vol_disk_id) == volume_id:
                    json_response = {"volumeAttachment":
                                     {"device": "", "id": vol_disk_id,
                                      "serverId": instance_id,
                                      "volumeId": vol_disk_id}}
                    break
            if json_response:
                resp.body = json_response
            else:
                return error_handling.volume_fault(resp, 'Invalid volume id.',
                                                   code=HTTP.BAD_REQUEST)
        except Exception as e:
            return error_handling.volume_fault(resp, e.faultString)

    def on_delete(self, req, resp, tenant_id, instance_id, volume_id):
        """Detach the requested volume from the specified instance."""
        try:
            instance_id = int(instance_id)
        except Exception:
            return error_handling.not_found(resp,
                                            "Invalid instance ID specified.")

        if volume_id and len(volume_id) > OPENSTACK_VOLUME_UUID_LEN:
            return error_handling.bad_request(resp,
                                              message="Malformed request body")

        vdi_client = req.sl_client['Virtual_Disk_Image']

        # first let's check if the volume is already attached
        try:
            volinfo = vdi_client.getObject(id=volume_id, mask='blockDevices')
            blkDevices = volinfo['blockDevices']
            if len(blkDevices) > 0:
                guestId_list = [blkDevice['guestId'] for blkDevice
                                in blkDevices]
                for guest_id in guestId_list:
                    if guest_id == instance_id:
                        try:
                            # detach the volume here
                            vg_client = req.sl_client['Virtual_Guest']
                            vg_client.detachDiskImage(volume_id,
                                                      id=instance_id)
                            break
                        except Exception as e:
                            error_handling.volume_fault(resp,
                                                        e.faultString)
                    else:
                        return error_handling.volume_fault(
                            resp,
                            'The requested disk image is attached to another '
                            'guest and cannot be detached.',
                            code=HTTP.BAD_REQUEST)

        except Exception as e:
            return error_handling.volume_fault(resp, e.faultString,
                                               code=500)

        resp.status = HTTP.ACCEPTED


def format_volume_attachment(volume_id, instance_id, device_name):
    return {"device": device_name, "id": volume_id, "serverId": instance_id,
            "volumeId": volume_id}
