from spotty.config.validation import validate_config, get_instance_parameters_schema


def validate_instance_parameters(params: dict):
    from spotty.config.host_path_volume import HostPathVolume

    schema = get_instance_parameters_schema({}, HostPathVolume.TYPE_NAME)

    return validate_config(schema, params)
