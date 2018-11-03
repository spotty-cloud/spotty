import os
from schema import Schema, And, Use, Optional, Or, Regex
from spotty.helpers.config import validate_config


def validate_basic_config(data):
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
                                                      error='Invalid name for a Dockerfile')
                                                  ),
                Optional('volumeMounts'): (And(
                    [{
                        'name': And(Or(int, str), Use(str), Regex(r'^[\w-]+$')),
                        'mountPath': And(str,
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
                And(str, Regex(r'^[\w]+$')): object,  # TODO: check
            },
        }],
        Optional('scripts', default={}): {
            And(str, Regex(r'^[\w-]+$')): And(str, len),
        },
    })

    return validate_config(schema, data)
