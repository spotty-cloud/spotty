import os
from schema import Schema, Optional, And, Regex, Or, Use
from spotty.config.utils import validate_config


AMI_NAME_REGEX = r'^[\w\(\)\[\]\s\.\/\'@-]{3,128}$'
DEFAULT_AMI_NAME = 'SpottyAMI'


def validate_aws_instance_parameters(params):
    schema = Schema({
        'region': And(str, len),
        Optional('availabilityZone', default=''): str,
        Optional('subnetId', default=''): str,
        'instanceType': And(str, And(is_valid_instance_type, error='Invalid instance type.')),
        Optional('onDemandInstance', default=False): bool,
        Optional('amiName', default=DEFAULT_AMI_NAME): And(str, len, Regex(AMI_NAME_REGEX)),
        Optional('rootVolumeSize', default=0): And(Or(int, str), Use(str),
                                                   Regex(r'^\d+$', error='Incorrect value for "rootVolumeSize".'),
                                                   Use(int),
                                                   And(lambda x: x > 0,
                                                       error='"rootVolumeSize" should be greater than 0 or should '
                                                             ' not be specified.'),
                                                   ),
        # TODO: check that mountDir for dockerDataRoot exists
        Optional('dockerDataRoot', default=''): And(str,
                                                    And(os.path.isabs,
                                                        error='Use an absolute path when specifying a Docker '
                                                              'data root directory'),
                                                    Use(lambda x: x.rstrip('/')),
                                                ),
        Optional('maxPrice', default=0): And(Or(float, int, str), Use(str),
                                             Regex(r'^\d+(\.\d{1,6})?$', error='Incorrect value for "maxPrice".'),
                                             Use(float),
                                             And(lambda x: x > 0, error='"maxPrice" should be greater than 0 or '
                                                                        'should  not be specified.'),
                                             ),  # TODO: maxPrice can only be specified if spotInstance is true
        Optional('volumes', default=[]): And(
            [{
                'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                'parameters': {
                    Optional('mountDir', default=''): And(str, lambda x: x.startswith('/'),
                                                          Use(lambda x: x.rstrip('/'))),
                    Optional('snapshotName', default=''): str,
                    Optional('size', default=0): And(int, lambda x: x > 0),
                    Optional('deletionPolicy',
                             default='create_snapshot'): And(str, lambda x: x in ['create_snapshot', 'update_snapshot',
                                                                                  'retain', 'delete'],
                                                             error='Incorrect value for "deletionPolicy".'
                                                             ),
                }
            }],
            And(lambda x: len(x) < 12, error='Maximum 11 volumes are supported at the moment.'),
            # TODO:
            # And(lambda x: unique_name(x), error='Each volume should have a unique name.'),
        ),
        Optional('localSshPort', default=None): And(int, lambda x: 0 <= x <= 65535),
    })

    return validate_config(schema, params)


# def validate_ami_config(data):
#     schema = Schema({
#         'instance': {
#             'region': And(str, len),
#             Optional('availabilityZone', default=''): str,
#             Optional('subnetId', default=''): str,
#             'instanceType': And(str, len),
#             Optional('amiName', default=DEFAULT_AMI_NAME): And(str, len, Regex(AMI_NAME_REGEX)),
#             Optional('keyName', default=''): str,
#         },
#     }, ignore_extra_keys=True)
#
#     return validate_config(schema, data)

def is_gpu_instance(instance_type: str):
    return instance_type in [
        'p2.xlarge', 'p2.8xlarge', 'p2.16xlarge',
        'p3.2xlarge', 'p3.8xlarge', 'p3.16xlarge',
        'g3s.xlarge', 'g3.4xlarge', 'g3.8xlarge', 'g3.16xlarge',
    ]


def is_nitro_instance(instance_type):
    return instance_type in [
        'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge', 'c5.18xlarge',
        'c5d.large', 'c5d.xlarge', 'c5d.2xlarge', 'c5d.4xlarge', 'c5d.9xlarge', 'c5d.18xlarge',
        'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge', 'm5.12xlarge', 'm5.24xlarge',
        'm5d.large', 'm5d.xlarge', 'm5d.2xlarge', 'm5d.4xlarge', 'm5d.12xlarge', 'm5d.24xlarge',
        'i3.metal',
    ]


def is_valid_instance_type(instance_type: str):
    return instance_type in [
        't1.micro',
        't2.nano', 't2.micro', 't2.small', 't2.medium', 't2.large', 't2.xlarge', 't2.2xlarge',
        'm1.small', 'm1.medium', 'm1.large', 'm1.xlarge',
        'm3.medium', 'm3.large', 'm3.xlarge', 'm3.2xlarge',
        'm4.large', 'm4.xlarge', 'm4.2xlarge', 'm4.4xlarge', 'm4.10xlarge', 'm4.16xlarge',
        'm2.xlarge', 'm2.2xlarge', 'm2.4xlarge',
        'cr1.8xlarge',
        'r3.large', 'r3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge',
        'r4.large', 'r4.xlarge', 'r4.2xlarge', 'r4.4xlarge', 'r4.8xlarge', 'r4.16xlarge',
        'x1.16xlarge', 'x1.32xlarge',
        'x1e.xlarge', 'x1e.2xlarge', 'x1e.4xlarge', 'x1e.8xlarge', 'x1e.16xlarge', 'x1e.32xlarge',
        'i2.xlarge', 'i2.2xlarge', 'i2.4xlarge', 'i2.8xlarge',
        'i3.large', 'i3.xlarge', 'i3.2xlarge', 'i3.4xlarge', 'i3.8xlarge', 'i3.16xlarge', 'i3.metal',
        'hi1.4xlarge',
        'hs1.8xlarge',
        'c1.medium', 'c1.xlarge',
        'c3.large', 'c3.xlarge', 'c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge',
        'c4.large', 'c4.xlarge', 'c4.2xlarge', 'c4.4xlarge', 'c4.8xlarge',
        'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge', 'c5.18xlarge',
        'c5d.large', 'c5d.xlarge', 'c5d.2xlarge', 'c5d.4xlarge', 'c5d.9xlarge', 'c5d.18xlarge',
        'cc1.4xlarge',
        'cc2.8xlarge',
        'g2.2xlarge', 'g2.8xlarge',
        'g3s.xlarge', 'g3.4xlarge', 'g3.8xlarge', 'g3.16xlarge',
        'cg1.4xlarge',
        'p2.xlarge', 'p2.8xlarge', 'p2.16xlarge',
        'p3.2xlarge', 'p3.8xlarge', 'p3.16xlarge',
        'd2.xlarge', 'd2.2xlarge', 'd2.4xlarge', 'd2.8xlarge',
        'f1.2xlarge', 'f1.16xlarge',
        'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge', 'm5.12xlarge', 'm5.24xlarge',
        'm5d.large', 'm5d.xlarge', 'm5d.2xlarge', 'm5d.4xlarge', 'm5d.12xlarge', 'm5d.24xlarge',
        'h1.2xlarge', 'h1.4xlarge', 'h1.8xlarge', 'h1.16xlarge',
    ]
