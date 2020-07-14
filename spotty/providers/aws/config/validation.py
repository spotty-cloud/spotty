import os
from schema import Schema, Optional, And, Regex, Or, Use
from spotty.config.validation import validate_config, get_instance_parameters_schema, has_prefix


def validate_instance_parameters(params: dict):
    from spotty.providers.aws.config.ebs_volume import EbsVolume

    instance_parameters = {
        'region': And(str, Regex(r'^[a-z0-9-]+$')),
        Optional('availabilityZone', default=''): And(str, Regex(r'^[a-z0-9-]+$')),
        Optional('subnetId', default=''): And(str, Regex(r'^subnet-[a-z0-9]+$')),
        'instanceType': str,
        Optional('spotInstance', default=False): bool,
        Optional('amiName', default=None): And(str, len, Regex(r'^[\w\(\)\[\]\s\.\/\'@-]{3,128}$')),
        Optional('amiId', default=None): And(str, len, Regex(r'^ami-[a-z0-9]+$')),
        Optional('rootVolumeSize', default=0): And(Or(int, str), Use(str),
                                                   Regex(r'^\d+$', error='Incorrect value for "rootVolumeSize".'),
                                                   Use(int),
                                                   And(lambda x: x > 0,
                                                       error='"rootVolumeSize" should be greater than 0 or should '
                                                             'not be specified.'),
                                                   ),
        Optional('ports', default=[]): [And(int, lambda x: 0 < x < 65536)],
        Optional('maxPrice', default=0): And(Or(float, int, str), Use(str),
                                             Regex(r'^\d+(\.\d{1,6})?$', error='Incorrect value for "maxPrice".'),
                                             Use(float),
                                             And(lambda x: x > 0, error='"maxPrice" should be greater than 0 or '
                                                                        'should  not be specified.'),
                                             ),
        Optional('managedPolicyArns', default=[]): [str],
        Optional('instanceProfileArn', default=None): str,
    }

    volumes_checks = [
        And(lambda x: len(x) < 12, error='Maximum 11 volumes are supported at the moment.'),
        And(lambda x: not has_prefix([(volume['parameters']['mountDir'] + '/') for volume in x
                                      if volume['parameters'].get('mountDir')]),
            error='Mount directories cannot be prefixes for each other.'),
    ]

    instance_checks = [
        And(lambda x: not (x['maxPrice'] and not x['spotInstance']),
            error='"maxPrice" can be specified only for spot instances.'),
        And(lambda x: not (x['amiName'] and x['amiId']),
            error='"amiName" and "amiId" parameters cannot be used together.'),
    ]

    schema = get_instance_parameters_schema(instance_parameters, EbsVolume.TYPE_NAME, instance_checks, volumes_checks)

    return validate_config(schema, params)


def validate_ebs_volume_parameters(params: dict):
    from spotty.providers.aws.config.ebs_volume import EbsVolume

    old_deletion_policies_map = {
        'create_snapshot': EbsVolume.DP_CREATE_SNAPSHOT,
        'update_snapshot': EbsVolume.DP_UPDATE_SNAPSHOT,
        'retain': EbsVolume.DP_RETAIN,
        'delete': EbsVolume.DP_DELETE,
    }

    schema = Schema({
        Optional('volumeName', default=''): And(str, Regex(r'^[\w-]{1,255}$')),
        Optional('mountDir', default=''): And(
            str,
            And(os.path.isabs, error='Use absolute paths in the "mountDir" parameters'),
            Use(lambda x: x.rstrip('/'))
        ),
        Optional('size', default=0): And(int, lambda x: x > 0),
        # TODO: add the "iops" parameter to support the "io1" EBS volume type
        Optional('type', default='gp2'): lambda x: x in ['gp2', 'sc1', 'st1', 'standard'],
        Optional('deletionPolicy', default=EbsVolume.DP_RETAIN): And(
            str,
            lambda x: x in [EbsVolume.DP_CREATE_SNAPSHOT,
                            EbsVolume.DP_UPDATE_SNAPSHOT,
                            EbsVolume.DP_RETAIN,
                            EbsVolume.DP_DELETE] + list(old_deletion_policies_map.keys()),
            Use(lambda x: old_deletion_policies_map.get(x, x)),
            error='Incorrect value for "deletionPolicy".',
        ),
    })

    return validate_config(schema, params)
