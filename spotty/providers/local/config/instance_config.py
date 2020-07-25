import os
from typing import List
from spotty.config.abstract_instance_config import AbstractInstanceConfig, VolumeMount
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.config.container_config import PROJECT_VOLUME_MOUNT_NAME
from spotty.config.project_config import ProjectConfig
from spotty.config.host_path_volume import HostPathVolume
from spotty.providers.local.config.validation import validate_instance_parameters


class InstanceConfig(AbstractInstanceConfig):

    def __init__(self, instance_config: dict, project_config: ProjectConfig):
        super().__init__(instance_config, project_config)

    def _validate_instance_params(self, params: dict):
        # validate the config and fill missing parameters with the default values
        return validate_instance_parameters(params)

    def _get_instance_volumes(self) -> List[AbstractInstanceVolume]:
        volumes = []
        for volume_config in self._params['volumes']:
            volume_type = volume_config['type']
            if volume_type == HostPathVolume.TYPE_NAME:
                volumes.append(HostPathVolume(volume_config, self.project_config.project_dir))
            else:
                raise ValueError('Volume type "%s" is not supported.' % volume_type)

        return volumes

    def _get_volume_mounts(self, volumes: List[AbstractInstanceVolume]) -> List[VolumeMount]:
        volume_mounts = super()._get_volume_mounts(volumes)

        # ignore a volume that matches the container project directory
        volume_mounts = [volume_mount for volume_mount in volume_mounts
                         if os.path.relpath(self.container_config.project_dir, volume_mount.mount_path) != '.']

        # mount the local project directory to the container
        volume_mounts.append(VolumeMount(
            name=PROJECT_VOLUME_MOUNT_NAME,
            host_path=self.project_config.project_dir,
            mount_path=self.container_config.project_dir,
            mode='rw',
            hidden=True,
        ))

        return volume_mounts

    @property
    def user(self) -> str:
        return ''
