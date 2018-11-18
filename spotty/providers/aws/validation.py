import os
from schema import Schema, Optional, And, Regex, Or, Use
from spotty.helpers.config import validate_config
from spotty.providers.aws.helpers.resources import is_valid_instance_type


AMI_NAME_REGEX = r'^[\w\(\)\[\]\s\.\/\'@-]{3,128}$'
DEFAULT_AMI_NAME = 'SpottyAMI'


def validate_aws_instance_parameters(params):
    schema = Schema({
        'region': And(str, len),
        Optional('availabilityZone', default=''): str,
        Optional('subnetId', default=''): str,
        'instanceType': And(str, And(is_valid_instance_type, error='Invalid instance type.')),
        Optional('spotInstance', default=True): bool,
        Optional('amiName', default=DEFAULT_AMI_NAME): And(str, len, Regex(AMI_NAME_REGEX)),
        Optional('keyName', default=''): str,
        Optional('rootVolumeSize', default=0): And(Or(int, str), Use(str),
                                                   Regex(r'^\d+$', error='Incorrect value for "rootVolumeSize".'),
                                                   Use(int),
                                                   And(lambda x: x > 0,
                                                       error='"rootVolumeSize" should be greater than 0 or should '
                                                             ' not be specified.'),
                                                   ),
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
                    Optional('directory', default=''): And(str, lambda x: x.startswith('/'),
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
