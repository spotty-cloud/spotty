from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.local.config.validation import validate_host_path_volume_parameters


class HostPathVolume(AbstractInstanceVolume):

    def __init__(self, volume_config: dict, project_name: str, instance_name: str):
        self._name = volume_config['name']
        self._params = validate_host_path_volume_parameters(volume_config['parameters'])

        self._project_name = project_name
        self._instance_name = instance_name

    @property
    def title(self):
        return 'HostPath volume'

    @property
    def name(self):
        return self._name

    @property
    def deletion_policy_title(self) -> str:
        return ''

    @property
    def host_path(self) -> str:
        """A path on the host OS that will be mounted to the container."""
        return self._params['path']
