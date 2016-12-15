from jumpgate.image.drivers.sl import images as glance_images

# http://docs.openstack.org/developer/glance/statuses.html
# http://developer.openstack.org/api-ref/compute/#show-image-details
IMAGE_STATUS_MAP = {
    glance_images.GLANCE_IMAGE_STATUS_ACTIVE: 'ACTIVE',
    glance_images.GLANCE_IMAGE_STATUS_DEACTIVATED: 'UNKNOWN',
}


class ComputeImageShow(object):
    """Handles the compute image GET proxy for showing image details.

    This calls the ImageV2 handler and then has to massage the results
    to fit the nova GET /images proxy API.

    Note that this proxy API in nova is deprecated upstream but it's part of
    restack/defcore so we have to support it for interoperability.
    """

    def __init__(self, app):
        self.image_controller = glance_images.ImageV2(app)

    def on_get(self, req, resp, image_guid, tenant_id=None):
        self.image_controller.on_get(req, resp, image_guid, tenant_id)
        # exit early if getting the image details failed
        if resp.status != 200:
            return
        image = resp.body

        # server and OS-DCF:diskConfig are not required and we don't have
        # compatible SL values to use anyway so we omit them.
        proxy_details = {
            'id': image['id'],
            'name': image['name'],
            'links': image['links'],
            'status': IMAGE_STATUS_MAP.get(image['status']),
            'updated': image['updated'],
            'created': image['created'],
            'minDisk': image['min_disk'],
            'minRam': image['min_ram'],
            'progress': image['progress'],
            'metadata': image['metadata'],
            'OS-EXT-IMG-SIZE:size': image['size'],
        }

        resp.body = {'image': proxy_details}
