import os
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.config.validation import validate_host_path_volume_parameters


class HostPathVolume(AbstractInstanceVolume):

    TYPE_NAME = 'HostPath'

    def __init__(self, volume_config: dict, base_dir: str = None):
        super().__init__(volume_config)

        self._base_dir = base_dir

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
        path = os.path.expanduser(self._params['path'])
        if not os.path.isabs(path):
            if self._base_dir is not None:
                path = os.path.join(self._base_dir, path)
            else:
                raise ValueError('Use absolute path for the "%s" volume.' % self.name)

        return path
