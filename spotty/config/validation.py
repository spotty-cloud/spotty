import os
from typing import List
from schema import Schema, And, Use, Optional, Or, Regex, Hook, SchemaError, SchemaForbiddenKeyError


DEFAULT_CONTAINER_NAME = 'default'


def validate_basic_config(data):

    container = And(
        {
            Optional('name', default=DEFAULT_CONTAINER_NAME): And(str, Regex(r'^[\w-]+$')),
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
                                              ),
            Optional('runAsHostUser', default=False): bool,
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
            Optional('env', default={}): {
                And(str, Regex(r'^[a-zA-Z_]+[a-zA-Z0-9_]*$')): str,
            },
            Optional('hostNetwork', default=False): bool,
            Optional('ports', default=[]): [{
                'containerPort': And(int, lambda x: 0 < x < 65536),
                Optional('hostPort', default=None): And(int, lambda x: 0 < x < 65536),
            }],
            Optional('commands', default=''): str,
            # TODO: allow to use only certain runtime parameters
            Optional('runtimeParameters', default=[]): And([str], Use(lambda x: [p.strip() for p in x])),
        },
        And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
        And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
        And(lambda x: not (x['hostNetwork'] and x['ports']),
            error='Published ports and the host network mode cannot be used together.'),
    )

    schema = Schema({
        'project': {
            'name': And(str, Regex(r'^[a-zA-Z0-9][a-zA-Z0-9-]{,26}[a-zA-Z0-9]$')),
            Optional('syncFilters', default=[]): And(
                [And(
                    {
                        Optional('exclude'): [And(str, len, And(lambda x: '**' not in x,
                                                                error='Use single asterisks ("*") in sync filters'))],
                        Optional('include'): [And(str, len, And(lambda x: '**' not in x,
                                                                error='Use single asterisks ("*") in sync filters'))],
                    },
                    And(lambda x: x, error='Either "exclude" or "include" filter should be specified.'),
                    And(lambda x: not ('exclude' in x and 'include' in x),
                        error='"exclude" and "include" filters should be specified as different list items.'),
                )],
                error='"project.syncFilters" field must be a list.',
            )
        },
        WrongKey('container', error='Use "containers" field instead of "container".'): object,
        Optional('containers', default=[]): And(
            [container],
            And(lambda x: is_unique_value(x, 'name'), error='Each container must have a unique name.'),
            error='"containers" field must be a list.',
        ),
        WrongKey('instance', error='Use "instances" field instead of "instance".'): object,
        'instances': And(
            [{
                'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                'provider': str,
                Optional('parameters', default={}): {
                    And(str, Regex(r'^[\w]+$')): object,
                }
            }],
            And(lambda x: len(x), error='At least one instance must be specified in the configuration file.'),
            And(lambda x: is_unique_value(x, 'name'), error='Each instance must have a unique name.'),
        ),
        Optional('scripts', default={}): {
            And(str, Regex(r'^[\w-]+$')): And(str, len),
        },
    })

    return validate_config(schema, data)


def validate_host_path_volume_parameters(params: dict):
    schema = Schema({
        'path': And(str, Use(lambda x: x.rstrip('/'))),
    })

    return validate_config(schema, params)


def get_instance_parameters_schema(instance_parameters: dict, default_volume_type: str,
                                   instance_checks: list = None, volumes_checks: list = None):
    if not instance_checks:
        instance_checks = []

    if not volumes_checks:
        volumes_checks = []

    schema = Schema(And(
        {
            **instance_parameters,
            Optional('containerName', default=None): And(str, Regex(r'^[\w-]+$')),
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
                        And(str, Regex(r'^[\w]+$')): object,
                    },
                }],
                And(lambda x: is_unique_value(x, 'name'), error='Each instance volume must have a unique name.'),
                *volumes_checks,
            ),
            Optional('localSshPort', default=None): Or(None, And(int, lambda x: 0 < x < 65536)),
            Optional('commands', default=''): str,
        },
        And(lambda x: not x['dockerDataRoot'] or any([True for v in x['volumes'] if v['parameters']['mountDir'] and
                                                      is_subdir(x['dockerDataRoot'], v['parameters']['mountDir'])]),
            error='The "mountDir" of one of the volumes must be a prefix for the "dockerDataRoot" path.'),
        *instance_checks
    ))

    return schema


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
        raise ValueError('Validation error: ' + (e.errors[-1] if e.errors[-1] else e.autos[-1]))

    return validated


class WrongKey(Hook):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, handler=self.raise_error)

    def raise_error(self, key, *args):
        raise SchemaForbiddenKeyError(self._error)
