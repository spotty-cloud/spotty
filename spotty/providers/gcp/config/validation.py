from schema import Schema, Optional, And, Regex, Or, Use
from spotty.config.validation import validate_config, get_instance_parameters_schema

DEFAULT_IMAGE_NAME = 'spotty'
IMAGE_NAME_REGEX = r'^[\w-]+$'


def validate_instance_parameters(params: dict):
    from spotty.providers.gcp.config.instance_config import VOLUME_TYPE_DISK

    instance_parameters = {
        'projectId': str,  # todo: remove it, project ID is a part of a service account credentials
        'zone': And(str, Regex(r'^[a-z0-9-]+$')),
        'machineType': And(str, And(is_valid_machine_type, error='Invalid instance type.')),
        Optional('gpu', default=None): {
            'type': And(str, And(is_valid_gpu_type, error='Invalid GPU type.')),
            Optional('count', default=1): int,
        },
        Optional('onDemandInstance', default=False): bool,
        Optional('imageName', default=DEFAULT_IMAGE_NAME): And(str, len, Regex(IMAGE_NAME_REGEX)),
        Optional('bootDiskSize', default=0): And(Or(int, str), Use(str),
                                                 Regex(r'^\d+$', error='Incorrect value for "bootDiskSize".'),
                                                 Use(int),
                                                 And(lambda x: x > 0,
                                                     error='"rootVolumeSize" should be greater than 0 or should '
                                                           'not be specified.'),
                                                 ),
    }

    instance_checks = [
        And(lambda x: not x['gpu'] or is_gpu_machine_type(x['machineType']),
            error='GPU cannot be attached to shared-core or memory-optimized machine types'),
    ]

    schema = get_instance_parameters_schema(instance_parameters, VOLUME_TYPE_DISK, instance_checks, [])

    return validate_config(schema, params)


def validate_disk_volume_parameters(params: dict):
    from spotty.providers.gcp.deployment.project_resources.disk_volume import DiskVolume

    schema = Schema({
        Optional('diskName', default=''): And(str, Regex(r'^[\w-]{1,255}$')),
        Optional('mountDir', default=''): str,  # all the checks happened in the base configuration
        Optional('size', default=0): And(int, lambda x: x > 0),
        Optional('deletionPolicy', default=DiskVolume.DP_CREATE_SNAPSHOT): And(
            str,
            lambda x: x in [DiskVolume.DP_CREATE_SNAPSHOT,
                            DiskVolume.DP_UPDATE_SNAPSHOT,
                            DiskVolume.DP_RETAIN,
                            DiskVolume.DP_DELETE], error='Incorrect value for "deletionPolicy".'
        ),
    })

    return validate_config(schema, params)


def is_valid_gpu_type(gpu_type: str):
    return gpu_type in [
        'nvidia-tesla-p4', 'nvidia-tesla-v100', 'nvidia-tesla-p100', 'nvidia-tesla-k80',
        'nvidia-tesla-p4-vws', 'nvidia-tesla-p100-vws',
    ]


def is_valid_machine_type(instance_type: str):
    return instance_type in [
        'n1-standard-1', 'n1-standard-2', 'n1-standard-4', 'n1-standard-8', 'n1-standard-16', 'n1-standard-32', 'n1-standard-64', 'n1-standard-96',
        'n1-highmem-2', 'n1-highmem-4', 'n1-highmem-8', 'n1-highmem-16', 'n1-highmem-32', 'n1-highmem-64', 'n1-highmem-96',
        'n1-highcpu-2', 'n1-highcpu-4', 'n1-highcpu-8', 'n1-highcpu-16', 'n1-highcpu-32', 'n1-highcpu-64', 'n1-highcpu-96',
        'f1-micro', 'g1-small',
        'n1-ultramem-40', 'n1-ultramem-80', 'n1-ultramem-160',
        'n1-megamem-96',
    ]


def is_gpu_machine_type(instance_type: str):
    return is_valid_machine_type(instance_type) and instance_type not in [
        # shared-core machine types
        'f1-micro', 'g1-small',
        # memory-optimized machine types
        'n1-ultramem-40', 'n1-ultramem-80', 'n1-ultramem-160',
        'n1-megamem-96',
    ]