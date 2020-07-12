from schema import And, Optional
from spotty.config.validation import validate_config, get_instance_parameters_schema


def validate_instance_parameters(params: dict):
    from spotty.config.host_path_volume import HostPathVolume

    instance_parameters = {
        'username': str,
        'hostname': str,
        Optional('port', default=22): And(int, lambda x: 0 <= x <= 65535),
        'keyPath': str,
    }

    schema = get_instance_parameters_schema(instance_parameters, HostPathVolume.TYPE_NAME)

    return validate_config(schema, params)
