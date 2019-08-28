from schema import Schema, Optional, And, Regex, Or, Use
from spotty.config.validation import validate_config, get_instance_parameters_schema


def validate_instance_parameters(params: dict):
    from spotty.providers.aws.config.instance_config import VOLUME_TYPE_EBS

    instance_parameters = {
        'region': And(str, Regex(r'^[a-z0-9-]+$')),
        Optional('availabilityZone', default=''): And(str, Regex(r'^[a-z0-9-]+$')),
        Optional('subnetId', default=''): And(str, Regex(r'^subnet-[a-z0-9]+$')),
        'instanceType': str,
        Optional('onDemandInstance', default=False): bool,
        Optional('amiName', default=None): And(str, len, Regex(r'^[\w\(\)\[\]\s\.\/\'@-]{3,128}$')),
        Optional('amiId', default=None): And(str, len, Regex(r'^ami-[a-z0-9]+$')),
        Optional('rootVolumeSize', default=0): And(Or(int, str), Use(str),
                                                   Regex(r'^\d+$', error='Incorrect value for "rootVolumeSize".'),
                                                   Use(int),
                                                   And(lambda x: x > 0,
                                                       error='"rootVolumeSize" should be greater than 0 or should '
                                                             'not be specified.'),
                                                   ),
        Optional('maxPrice', default=0): And(Or(float, int, str), Use(str),
                                             Regex(r'^\d+(\.\d{1,6})?$', error='Incorrect value for "maxPrice".'),
                                             Use(float),
                                             And(lambda x: x > 0, error='"maxPrice" should be greater than 0 or '
                                                                        'should  not be specified.'),
                                             ),
        Optional('managedPolicyArns', default=[]): [str],
    }

    volumes_checks = [
        And(lambda x: len(x) < 12, error='Maximum 11 volumes are supported at the moment.'),
    ]

    instance_checks = [
        And(lambda x: not (x['onDemandInstance'] and x['maxPrice']),
            error='"maxPrice" cannot be specified for on-demand instances.'),
        And(lambda x: not (x['amiName'] and x['amiId']),
            error='"amiName" and "amiId" parameters cannot be used together.'),
    ]

    schema = get_instance_parameters_schema(instance_parameters, VOLUME_TYPE_EBS, instance_checks, volumes_checks)

    return validate_config(schema, params)


def validate_ebs_volume_parameters(params: dict):
    from spotty.providers.aws.deployment.project_resources.ebs_volume import EbsVolume

    schema = Schema({
        Optional('volumeName', default=''): And(str, Regex(r'^[\w-]{1,255}$')),
        Optional('mountDir', default=''): str,  # all the checks happened in the base configuration
        Optional('size', default=0): And(int, lambda x: x > 0),
        # TODO: add the "iops" parameter to support the "io1" EBS volume type
        Optional('type', default='gp2'): lambda x: x in ['gp2', 'sc1', 'st1', 'standard'],
        Optional('deletionPolicy', default=EbsVolume.DP_CREATE_SNAPSHOT): And(
            str,
            lambda x: x in [EbsVolume.DP_CREATE_SNAPSHOT,
                            EbsVolume.DP_UPDATE_SNAPSHOT,
                            EbsVolume.DP_RETAIN,
                            EbsVolume.DP_DELETE], error='Incorrect value for "deletionPolicy".'
        ),
    })

    return validate_config(schema, params)


def is_gpu_instance(instance_type: str):
    # a list of GPU instance from: https://aws.amazon.com/ec2/instance-types/#Accelerated_Computing
    return instance_type in [
        'p2.xlarge', 'p2.8xlarge', 'p2.16xlarge',
        'p3.2xlarge', 'p3.8xlarge', 'p3.16xlarge', 'p3dn.24xlarge',
        'g3s.xlarge', 'g3.4xlarge', 'g3.8xlarge', 'g3.16xlarge',
    ]


def is_nitro_instance(instance_type):
    # a list of Nitro-based instances from:
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html#ec2-nitro-instances
    nitro_prefixes = ['a1', 'c5', 'c5d', 'c5n', 'i3en', 'm5', 'm5a', 'm5ad', 'm5d', 'r5', 'r5a', 'r5ad', 'r5d',
                         't3', 't3a', 'z1d']
    nitro_types = ['p3dn.24xlarge', 'i3.metal', 'u-6tb1.metal', 'u-9tb1.metal', 'u-12tb1.metal']

    return any(instance_type.startswith(prefix + '.') for prefix in nitro_prefixes) or instance_type in nitro_types
