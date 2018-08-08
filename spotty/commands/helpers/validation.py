from schema import Schema, And, Use, Optional, SchemaError, Or, Regex
from spotty.commands.helpers.resources import is_valid_instance_type

AMI_NAME_REGEX = r'^[\w\(\)\[\]\s\.\/\'@-]{3,128}$'
DEFAULT_AMI_NAME = 'SpottyAMI'


def _validate(schema: Schema, data):
    try:
        validated = schema.validate(data)
    except SchemaError as e:
        raise ValueError(e.errors[-1] if e.errors[-1] else e.autos[-1])

    return validated


def validate_instance_config(data):
    schema = Schema({
        'project': {
            'name': And(str, Regex(r'^[a-zA-Z0-9][a-zA-Z0-9-]{,26}[a-zA-Z0-9]$')),
            'remoteDir': And(str, Use(lambda x: x.rstrip('/'))),
            Optional('syncFilters', default=[]): [And(
                {
                    Optional('exclude'): [And(str, len)],
                    Optional('include'): [And(str, len)],
                },
                And(lambda x: x, error='Either "exclude" or "include" filter should be specified.'),
                And(lambda x: not ('exclude' in x and 'include' in x), error='"exclude" and "include" filters should '
                                                                             'be specified as different list items.'),
            )]
        },
        'instance': {
            'region': And(str, len),
            'instanceType': And(str, And(is_valid_instance_type, error='Invalid instance type.')),
            Optional('amiName', default=DEFAULT_AMI_NAME): And(str, len, Regex(AMI_NAME_REGEX)),
            Optional('keyName', default=''): str,
            Optional('rootVolumeSize', default=0): And(Or(int, str), Use(str),
                                                       Regex(r'^\d+$', error='Incorrect value for "rootVolumeSize".'),
                                                       Use(int),
                                                       And(lambda x: x > 0,
                                                           error='"rootVolumeSize" should be greater than 0 or should '
                                                                 ' not be specified.'),
                                                       ),
            Optional('maxPrice', default=0): And(Or(float, int, str), Use(str),
                                                 Regex(r'^\d+(\.\d{1,6})?$', error='Incorrect value for "maxPrice".'),
                                                 Use(float),
                                                 And(lambda x: x > 0, error='"maxPrice" should be greater than 0 or '
                                                                            'should  not be specified.'),
                                                 ),
            'volumes': And(
                [{
                    Optional('snapshotName', default=''): str,
                    'directory': And(str, Use(lambda x: x.rstrip('/'))),
                    Optional('size', default=0): And(int, lambda x: x > 0),
                    Optional('deletionPolicy', default='snapshot'): And(str, lambda x: x in ['snapshot', 'delete']),
                }],
                And(len, error='Volume configuration is required.'),
                And(lambda x: len(x) == 1, error='Only one volume is supported at the moment.'),
            ),
            'docker': And(
                {
                    Optional('image', default=''): str,
                    Optional('file', default=''): str,
                    Optional('workingDir', default='/root'): str,
                    Optional('dataRoot', default=''): And(str, Use(lambda x: x.rstrip('/'))),
                    Optional('commands', default=''): str,
                },
                And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
                And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
            ),
            Optional('ports', default=[]): [And(int, lambda x: 0 <= x <= 65535)],
        },
        Optional('scripts', default={}): {
            And(str, Regex(r'^[\w-]+$')): And(str, len),
        },
    })

    return _validate(schema, data)


def validate_ami_config(data):
    schema = Schema({
        'instance': {
            'region': And(str, len),
            'instanceType': And(str, len),
            Optional('amiName', default=DEFAULT_AMI_NAME): And(str, len, Regex(AMI_NAME_REGEX)),
            Optional('keyName', default=''): str,
        },
    }, ignore_extra_keys=True)

    return _validate(schema, data)


def validate_logs_config(data):
    schema = Schema({
        'instance': {
            'region': And(str, len),
        },
    }, ignore_extra_keys=True)

    return _validate(schema, data)
