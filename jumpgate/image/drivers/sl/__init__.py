from jumpgate.common import sl as sl_common
from jumpgate.image.drivers.sl import images
from jumpgate.image.drivers.sl import versions


def setup_routes(app, disp):
    # Version index routes (they are the same)
    # This handles /
    disp.set_handler('index', versions.Index(app))
    # This handles /versions
    disp.set_handler('versions', versions.Index(app))

    # V2 Routes
    # FIXME(mriedem): There is no v2 route in glance upstream, see bug:
    # https://bugs.launchpad.net/glance/+bug/1632742
    # disp.set_handler('v2_version', versions.VersionV2(app))
    disp.set_handler('v2_image', images.ImageV2(app))
    disp.set_handler('v2_images', images.ImagesV2(app))
    disp.set_handler('v2_images_detail', images.ImagesV2(app, detail=True))
    disp.set_handler('v2_schema_image', images.SchemaImageV2())
    disp.set_handler('v2_schema_member', images.SchemaMemberV2())
    disp.set_handler('v2_schema_members', images.SchemaMembersV2())
    disp.set_handler('v2_schema_images', images.SchemaImagesV2())

    # V1 Routes
    # NOTE(mriedem): The image v1 route is actually weird, it does a GET on
    # /images.
    disp.set_handler('v1_version', images.ImagesV1(app))
    disp.set_handler('v1_image', images.ImageV1(app))
    disp.set_handler('v1_images', images.ImagesV1(app))
    disp.set_handler('v1_images_detail', images.ImagesV1(app))

    sl_common.add_hooks(app)
