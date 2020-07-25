import os
from typing import List
from spotty.config.abstract_instance_config import AbstractInstanceConfig
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.config.project_config import ProjectConfig
from spotty.config.host_path_volume import HostPathVolume
from spotty.providers.remote.config.validation import validate_instance_parameters


class InstanceConfig(AbstractInstanceConfig):

    def __init__(self, instance_config: dict, project_config: ProjectConfig):
        super().__init__(instance_config, project_config)

    def _validate_instance_params(self, params: dict):
        # validate the config and fill missing parameters with the default values
        return validate_instance_parameters(params)

    @property
    def user(self) -> str:
        return self._params['user']

    @property
    def host(self) -> str:
        return self._params['host']

    @property
    def port(self) -> int:
        return self._params['port']

    @property
    def key_path(self) -> str:
        key_path = os.path.expanduser(self._params['keyPath'])
        if not os.path.isabs(key_path):
            key_path = os.path.join(self.project_config.project_dir, key_path)

        key_path = os.path.normpath(key_path)

        return key_path

    def _get_instance_volumes(self) -> List[AbstractInstanceVolume]:
        volumes = []
        for volume_config in self._params['volumes']:
            volume_type = volume_config['type']
            if volume_type == HostPathVolume.TYPE_NAME:
                volumes.append(HostPathVolume(volume_config))
            else:
                raise ValueError('Volume type "%s" is not supported.' % volume_type)

        return volumes
