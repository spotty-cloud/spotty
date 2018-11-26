from schema import SchemaError, Schema
from spotty.utils import filter_list


def get_instance_config(instance_configs, instance_name):
    if not instance_name:
        instance_config = instance_configs[0]
    else:
        instance_configs = filter_list(instance_configs, 'name', instance_name)
        if not instance_configs:
            raise ValueError('Instance "%s" not found in the configuration file' % instance_name)

        instance_config = instance_configs[0]

    return instance_config


def validate_config(schema: Schema, config):
    try:
        validated = schema.validate(config)
    except SchemaError as e:
        raise ValueError(e.errors[-1] if e.errors[-1] else e.autos[-1])

    return validated
