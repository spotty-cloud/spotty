import logging
import os
from typing import List
from schema import Schema, And, Use, Optional, Or, Regex, SchemaError


def validate_basic_config(data, project_dir):
    is_old_config = 'instance' in data and 'container' not in data
    if is_old_config:
        logging.warning('The format of the configuration file that you\'re using is deprecated and won\'t be '
                        'supported in the future versions of Spotty.')

        data = convert_old_config(validate_old_config(data, project_dir))

    schema = Schema({
        'project': {
            'name': And(str, Regex(r'^[a-zA-Z0-9][a-zA-Z0-9-]{,26}[a-zA-Z0-9]$')),
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
        'container': And(
            {
                'projectDir': And(str,
                                  And(os.path.isabs,
                                      error='Use an absolute path when specifying the project directory'),
                                  Use(lambda x: x.rstrip('/'))
                                  ),
                Optional('image', default=''): And(str, len),
                Optional('file', default=''): And(str,  # TODO: a proper regex that the filename is valid
                                                  Regex(r'^[\w\.\/@-]*$',
                                                        error='Invalid name for a Dockerfile'),
                                                  And(lambda x: not x.endswith('/'),
                                                      error='Invalid name for a Dockerfile'),
                                                  And(lambda x: not os.path.isabs(x),
                                                      error='Path to the Dockerfile should be relative to the '
                                                            'project\'s root directory.'),
                                                  And(lambda x: os.path.isfile(os.path.join(project_dir, x)),
                                                      error='Dockerfile not found.'),
                                                  ),
                Optional('volumeMounts', default=[]): (And(
                    [{
                        'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                        'mountPath': And(
                            str,
                            And(os.path.isabs, error='Use an absolute path when specifying a mount directory'),
                            Use(lambda x: x.rstrip('/')),
                        ),
                    }],
                    And(lambda x: is_unique_value(x, 'name'),
                        error='Each volume mount must have a unique name.'),
                    And(lambda x: not has_prefix([(volume['mountPath'] + '/') for volume in x]),
                        error='Volume mount paths cannot be prefixes for each other.'),
                )),
                Optional('workingDir', default=''): And(str,
                                                        And(os.path.isabs,
                                                            error='Use an absolute path when specifying a '
                                                                  'working directory'),
                                                        Use(lambda x: x.rstrip('/'))
                                                        ),
                Optional('commands', default=''): str,
                Optional('ports', default=[]): [And(int, lambda x: 0 <= x <= 65535)],
                Optional('runtimeParameters', default=[]): [str],
            },
            And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
            And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
        ),
        'instances': And(
            [{
                'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                'provider': str,
                'parameters': And({
                    And(str, Regex(r'^[\w]+$')): object,
                }, error='Instance parameters are not specified')
            }],
            And(lambda x: is_unique_value(x, 'name'), error='Each instance must have a unique name.'),
        ),
        Optional('scripts', default={}): {
            And(str, Regex(r'^[\w-]+$')): And(str, len),
        },
    })

    return validate_config(schema, data)


def get_instance_parameters_schema(instance_parameters: dict, default_volume_type: str,
                                   instance_checks: list = None, volumes_checks: list = None):
    if not instance_checks:
        instance_checks = []

    if not volumes_checks:
        volumes_checks = []

    schema = Schema(And(
        {
            **instance_parameters,
            Optional('dockerDataRoot', default=''): And(
                str,
                And(os.path.isabs, error='Use an absolute path when specifying a Docker data root directory'),
                Use(lambda x: x.rstrip('/')),
            ),
            Optional('volumes', default=[]): And(
                [{
                    'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                    Optional('type', default=default_volume_type): str,
                    Optional('parameters', default={}): {
                        Optional('mountDir', default=''): And(
                            str,
                            And(os.path.isabs, error='Use absolute paths for mount directories'),
                            Use(lambda x: x.rstrip('/'))
                        ),
                        And(str, Regex(r'^[\w]+$')): object,
                    },
                }],
                And(lambda x: is_unique_value(x, 'name'), error='Each instance volume must have a unique name.'),
                And(lambda x: not has_prefix([(volume['parameters']['mountDir'] + '/') for volume in x
                                              if volume['parameters']['mountDir']]),
                    error='Mount directories cannot be prefixes for each other.'),
                *volumes_checks,
            ),
            Optional('localSshPort', default=None): Or(None, And(int, lambda x: 0 <= x <= 65535)),
        },
        And(lambda x: not x['dockerDataRoot'] or
                      [True for v in x['volumes'] if v['parameters']['mountDir'] and
                       is_subdir(x['dockerDataRoot'], v['parameters']['mountDir'])],
            error='The "mountDir" of one of the volumes must be a prefix for the "dockerDataRoot" path.'),
        *instance_checks
    ))

    return schema


def validate_old_config(data, project_dir):
    schema = Schema({
        'project': {
            'name': And(str, Regex(r'^[a-zA-Z0-9][a-zA-Z0-9-]{,26}[a-zA-Z0-9]$')),
            'remoteDir': And(str,
                             And(os.path.isabs,
                                 error='Use an absolute path when specifying a remote directory'),
                             Use(lambda x: x.rstrip('/'))
                             ),
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
            Optional('availabilityZone', default=''): str,
            Optional('subnetId', default=''): str,
            'instanceType': str,
            Optional('amiName', default='SpottyAMI'): str,
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
            Optional('volumes', default=[]): And(
                [{
                    Optional('name', default=''): And(str, Regex(r'^[\w-]{1,255}$')),
                    'directory': And(str, lambda x: x.startswith('/'), Use(lambda x: x.rstrip('/'))),
                    Optional('size', default=0): And(int, lambda x: x > 0),
                    Optional('deletionPolicy',
                             default='create_snapshot'): And(str, lambda x: x in ['create_snapshot', 'update_snapshot',
                                                                                  'retain', 'delete'],
                                                             error='Incorrect value for "deletionPolicy".'
                                                             ),
                }],
                And(lambda x: len(x) < 12, error='Maximum 11 volumes are supported at the moment.'),
            ),
            'docker': And(
                {
                    Optional('image', default=''): str,
                    Optional('file', default=''): And(str,  # TODO: a proper regex that the filename is valid
                                                      Regex(r'^[\w\.\/@-]*$',
                                                            error='Invalid name for a Dockerfile'),
                                                      And(lambda x: not x.endswith('/'),
                                                          error='Invalid name for a Dockerfile'),
                                                      And(lambda x: not os.path.isabs(x),
                                                          error='Path to the Dockerfile should be relative to the '
                                                                'project\'s root directory.'),
                                                      And(lambda x: os.path.isfile(os.path.join(project_dir, x)),
                                                          error='Dockerfile not found.'),
                                                      ),
                    Optional('workingDir', default=''): And(str,
                                                            And(os.path.isabs,
                                                                error='Use an absolute path when specifying a '
                                                                      'working directory'),
                                                            ),
                    Optional('dataRoot', default=''): And(str,
                                                          And(os.path.isabs,
                                                              error='Use an absolute path when specifying a Docker '
                                                                    'data root directory'),
                                                          Use(lambda x: x.rstrip('/')),
                                                          ),
                    Optional('commands', default=''): str,
                    Optional('runtimeParameters', default=[]): [str],
                },
                And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
                And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
            ),
            Optional('ports', default=[]): [And(int, lambda x: 0 <= x <= 65535)],
            Optional('localSshPort', default=None): And(int, lambda x: 0 <= x <= 65535),
        },
        Optional('scripts', default={}): {
            And(str, Regex(r'^[\w-]+$')): And(str, len),
        },
    })

    return validate_config(schema, data)


def convert_old_config(config):
    from spotty.providers.aws.config.instance_config import VOLUME_TYPE_EBS

    new_config = {
        'project': {
            'name': config['project']['name'],
            'syncFilters': config['project']['syncFilters'],
        },
        'container': {
            'projectDir': config['project']['remoteDir'],
            'image': config['instance']['docker']['image'],
            'file': config['instance']['docker']['file'],
            'volumeMounts': [{
                'name': volume['name'],
                'mountPath': volume['directory'],
            } for volume in config['instance']['volumes']],
            'workingDir': config['instance']['docker']['workingDir'],
            'commands': config['instance']['docker']['commands'],
            'ports': config['instance']['ports'],
            'runtimeParameters': config['instance']['docker']['runtimeParameters'],
        },
        'instances': [{
            'name': 'instance',
            'provider': 'aws',
            'parameters': {
                'region': config['instance']['region'],
                'availabilityZone': config['instance']['availabilityZone'],
                'subnetId': config['instance']['subnetId'],
                'instanceType': config['instance']['instanceType'],
                'amiName': config['instance']['amiName'],
                'rootVolumeSize': config['instance']['rootVolumeSize'],
                'dockerDataRoot': config['instance']['docker']['dataRoot'],
                'maxPrice': config['instance']['maxPrice'],
                'localSshPort': config['instance']['localSshPort'],
                'volumes': [{
                    'name': volume['name'],
                    'type': VOLUME_TYPE_EBS,
                    'parameters': {
                        'volumeName': volume['name'],
                        'mountDir': volume['directory'],
                        'size': volume['size'],
                        'deletionPolicy': volume['deletionPolicy'],
                    },
                } for volume in config['instance']['volumes']],
            },
        }],
        'scripts': config['scripts'],
    }

    def clear_empty_values(c):
        if isinstance(c, dict):
            c = {key: clear_empty_values(c[key]) for key in c if c[key]}
        elif isinstance(c, list):
            c = [clear_empty_values(row) for row in c]

        return c

    new_config = clear_empty_values(new_config)

    return new_config


def is_unique_value(x: List[dict], key):
    """Returns "True" if all values of the key in the list of dictionaries are unique."""
    return len(x) == len(set([v[key] for v in x]))


def has_prefix(x: list):
    """Returns "True" if some value in the list is a prefix for another value in this list."""
    for val in x:
        if len(list(filter(val.startswith, x))) > 1:
            return True

    return False


def is_subdir(subdir_path, dir_path):
    """Returns "True" if it's the second path parameter is a subdirectory of the first path parameter."""
    return (subdir_path.rstrip('/') + '/').startswith(dir_path.rstrip('/') + '/')


def validate_config(schema: Schema, config):
    try:
        validated = schema.validate(config)
    except SchemaError as e:
        raise ValueError(e.errors[-1] if e.errors[-1] else e.autos[-1])

    return validated
