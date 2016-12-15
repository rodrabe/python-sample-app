import os

from jumpgate.common import sl as sl_common
from jumpgate.volume.drivers.sl import index
from jumpgate.volume.drivers.sl import versionv2
from jumpgate.volume.drivers.sl import volumes
from jumpgate.volume.drivers.sl import volumesv2
from jumpgate.volume.drivers import volume_types_loader


def setup_routes(app, disp):
    # V2 Routes
    disp.set_handler('index', index.Index(app))
    disp.set_handler('v2_detail', versionv2.VersionV2(app))
    disp.set_handler('v2_volume', volumesv2.VolumesV2())
    # Need to implement at a later date
    # disp.set_handler('v2_volumes', volumesv2.VolumesV2())

    disp.set_handler('v2_volumes_detail', volumesv2.VolumesV2())
    # Load volume type list

    json_file = app.config.volume.volume_types
    if not os.path.exists(json_file):
        json_file = app.config.find_file(json_file)

    if json_file is None:
        raise ValueError('volume_types.json not found')

    with open(json_file) as jf:
        json_str = jf.read()

    vtl = volume_types_loader.VolumeTypesLoader(json_str)
    volume_types = vtl.get_volume_types()

    # V1 Routes
    disp.set_handler('v1_volumes_detail', volumes.VolumesV1(volume_types))
    disp.set_handler('v1_volume', volumes.VolumeV1())
    disp.set_handler('v1_volumes', volumes.VolumesV1(volume_types))
    disp.set_handler('v1_volume_types', volumes.VolumeTypesV1(volume_types))

    sl_common.add_hooks(app)
