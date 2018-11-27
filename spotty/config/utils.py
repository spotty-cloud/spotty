from schema import SchemaError, Schema


def validate_config(schema: Schema, config):
    try:
        validated = schema.validate(config)
    except SchemaError as e:
        raise ValueError(e.errors[-1] if e.errors[-1] else e.autos[-1])

    return validated
