from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.config.validation import validate_host_path_volume_parameters


class HostPathVolume(AbstractInstanceVolume):

    TYPE_NAME = 'HostPath'

    def _validate_volume_parameters(self, params: dict) -> dict:
        return validate_host_path_volume_parameters(params)

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
