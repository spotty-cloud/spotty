import os
from schema import Schema, And, Use, Optional, Or, Regex
from spotty.config.utils import validate_config


def validate_basic_config(data, project_dir):
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
                Optional('volumes'): (And(
                    [{
                        'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                        'path': And(str,
                                    And(os.path.isabs,
                                        error='Use an absolute path when specifying a mount directory'),
                                    Use(lambda x: x.rstrip('/'))
                                    ),
                    }],
                    # TODO:
                    # And(lambda x: no_prefixes(x), error='Mount paths cannot be prefixes for each other.'),
                    # And(lambda x: unique_name(x), error='Each volume mount should have unique name.'),
                )),
                Optional('workingDir', default=''): And(str,
                                                        And(os.path.isabs,
                                                            error='Use an absolute path when specifying a '
                                                                  'working directory'),
                                                        Use(lambda x: x.rstrip('/'))
                                                        ),
                Optional('commands', default=''): str,
                Optional('ports', default=[]): [And(int, lambda x: 0 <= x <= 65535)],
            },
            And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
            And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
        ),
        'instances': [{
            'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
            'provider': str,
            'parameters': {
                And(str, Regex(r'^[\w]+$')): object,
            },
        }],
        Optional('scripts', default={}): {
            And(str, Regex(r'^[\w-]+$')): And(str, len),
        },
    })

    return validate_config(schema, data)


# def validate_old_config(data):
#     schema = Schema({
#         'project': {
#             'name': And(str, Regex(r'^[a-zA-Z0-9][a-zA-Z0-9-]{,26}[a-zA-Z0-9]$')),
#             'remoteDir': And(str,
#                              And(os.path.isabs,
#                                  error='Use an absolute path when specifying a remote directory'),
#                              Use(lambda x: x.rstrip('/'))
#                              ),
#             Optional('syncFilters', default=[]): [And(
#                 {
#                     Optional('exclude'): [And(str, len)],
#                     Optional('include'): [And(str, len)],
#                 },
#                 And(lambda x: x, error='Either "exclude" or "include" filter should be specified.'),
#                 And(lambda x: not ('exclude' in x and 'include' in x), error='"exclude" and "include" filters should '
#                                                                              'be specified as different list items.'),
#             )]
#         },
#         'instance': {
#             'region': And(str, len),
#             Optional('availabilityZone', default=''): str,
#             Optional('subnetId', default=''): str,
#             'instanceType': And(str, And(is_valid_instance_type, error='Invalid instance type.')),
#             Optional('amiName', default=DEFAULT_AMI_NAME): And(str, len, Regex(AMI_NAME_REGEX)),
#             Optional('keyName', default=''): str,
#             Optional('rootVolumeSize', default=0): And(Or(int, str), Use(str),
#                                                        Regex(r'^\d+$', error='Incorrect value for "rootVolumeSize".'),
#                                                        Use(int),
#                                                        And(lambda x: x > 0,
#                                                            error='"rootVolumeSize" should be greater than 0 or should '
#                                                                  ' not be specified.'),
#                                                        ),
#             Optional('maxPrice', default=0): And(Or(float, int, str), Use(str),
#                                                  Regex(r'^\d+(\.\d{1,6})?$', error='Incorrect value for "maxPrice".'),
#                                                  Use(float),
#                                                  And(lambda x: x > 0, error='"maxPrice" should be greater than 0 or '
#                                                                             'should  not be specified.'),
#                                                  ),
#             Optional('volumes', default=[]): And(
#                 [{
#                     Optional('name', default=''): str,
#                     'directory': And(str, lambda x: x.startswith('/'), Use(lambda x: x.rstrip('/'))),
#                     Optional('size', default=0): And(int, lambda x: x > 0),
#                     Optional('deletionPolicy',
#                              default='create_snapshot'): And(str, lambda x: x in ['create_snapshot', 'update_snapshot',
#                                                                                   'retain', 'delete'],
#                                                              error='Incorrect value for "deletionPolicy".'
#                                                              ),
#                 }],
#                 And(lambda x: len(x) < 12, error='Maximum 11 volumes are supported at the moment.'),
#             ),
#             'docker': And(
#                 {
#                     Optional('image', default=''): str,
#                     Optional('file', default=''): And(str,  # TODO: a proper regex that the filename is valid
#                                                       Regex(r'^[\w\.\/@-]*$',
#                                                             error='Invalid name for a Dockerfile'),
#                                                       And(lambda x: not x.endswith('/'),
#                                                           error='Invalid name for a Dockerfile'),
#                                                       And(lambda x: not os.path.isabs(x),
#                                                           error='Path to the Dockerfile should be relative to the '
#                                                                 'project\'s root directory.'),
#                                                       ),
#                     Optional('workingDir', default=''): And(str,
#                                                             And(os.path.isabs,
#                                                                 error='Use an absolute path when specifying a '
#                                                                       'working directory'),
#                                                             ),
#                     Optional('dataRoot', default=''): And(str,
#                                                           And(os.path.isabs,
#                                                               error='Use an absolute path when specifying a Docker '
#                                                                     'data root directory'),
#                                                           Use(lambda x: x.rstrip('/')),
#                                                           ),
#                     Optional('commands', default=''): str,
#                 },
#                 And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
#                 And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
#             ),
#             Optional('ports', default=[]): [And(int, lambda x: 0 <= x <= 65535)],
#             Optional('localSshPort', default=None): And(int, lambda x: 0 <= x <= 65535),
#         },
#         Optional('scripts', default={}): {
#             And(str, Regex(r'^[\w-]+$')): And(str, len),
#         },
#     })
#
#     return _validate(schema, data)
