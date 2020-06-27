import os
from schema import Schema, And, Use
from spotty.config.validation import validate_config, get_instance_parameters_schema


def validate_instance_parameters(params: dict):
    from spotty.providers.local.config.instance_config import VOLUME_TYPE_HOST_PATH

    schema = get_instance_parameters_schema({}, VOLUME_TYPE_HOST_PATH)

    return validate_config(schema, params)


def validate_host_path_volume_parameters(params: dict):
    schema = Schema({
        'path': And(
            str,
            And(os.path.isabs, error='Use absolute path in the "path" parameter'),
            Use(lambda x: x.rstrip('/')),
        ),
    })

    return validate_config(schema, params)
