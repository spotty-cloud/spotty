import os
from schema import Schema, Optional, And, Regex, Or, Use
from spotty.config.validation import validate_config, get_instance_parameters_schema, has_prefix
from spotty.providers.gcp.config.image_uri import IMAGE_URI_REGEX


def validate_instance_parameters(params: dict):
    from spotty.providers.gcp.config.disk_volume import DiskVolume

    instance_parameters = {
        'zone': And(str, Regex(r'^[a-z0-9-]+$')),
        'machineType': str,
        Optional('gpu', default=None): {
            'type': str,
            Optional('count', default=1): int,
        },
        Optional('preemptibleInstance', default=False): bool,
        Optional('imageName', default=None): And(str, len, Regex(r'^[\w-]+$')),
        Optional('imageUri', default=None): And(str, len, Regex(IMAGE_URI_REGEX)),
        Optional('bootDiskSize', default=0): And(Or(int, str), Use(str),
                                                 Regex(r'^\d+$', error='Incorrect value for "bootDiskSize".'),
                                                 Use(int),
                                                 And(lambda x: x > 0,
                                                     error='"rootVolumeSize" should be greater than 0 or should '
                                                           'not be specified.'),
                                                 ),
        Optional('ports', default=[]): [And(int, lambda x: 0 < x < 65536)],
    }

    instance_checks = [
        And(lambda x: not (x['imageName'] and x['imageUri']),
            error='"imageName" and "imageUri" parameters cannot be used together.'),
    ]

    volume_checks = [
        And(lambda x: not has_prefix([(volume['parameters']['mountDir'] + '/') for volume in x
                                      if volume['parameters'].get('mountDir')]),
            error='Mount directories cannot be prefixes for each other.'),
    ]

    schema = get_instance_parameters_schema(instance_parameters, DiskVolume.TYPE_NAME, instance_checks, volume_checks)

    return validate_config(schema, params)


def validate_disk_volume_parameters(params: dict):
    from spotty.providers.gcp.config.disk_volume import DiskVolume

    schema = Schema({
        Optional('diskName', default=''): And(str, Regex(r'^[\w-]{1,255}$')),
        Optional('mountDir', default=''): And(
            str,
            And(os.path.isabs, error='Use absolute paths in the "mountDir" parameters'),
            Use(lambda x: x.rstrip('/'))
        ),
        Optional('size', default=0): And(int, lambda x: x > 0),
        Optional('deletionPolicy', default=DiskVolume.DP_RETAIN): And(
            str,
            lambda x: x in [DiskVolume.DP_CREATE_SNAPSHOT,
                            DiskVolume.DP_UPDATE_SNAPSHOT,
                            DiskVolume.DP_RETAIN,
                            DiskVolume.DP_DELETE], error='Incorrect value for "deletionPolicy".'
        ),
    })

    return validate_config(schema, params)
