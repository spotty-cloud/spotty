import os
from abc import ABC, abstractmethod
from collections import OrderedDict, namedtuple
from typing import List
from spotty.config.container_config import ContainerConfig
from spotty.config.project_config import ProjectConfig
from spotty.config.tmp_dir_volume import TmpDirVolume
from spotty.config.validation import DEFAULT_CONTAINER_NAME, is_subdir
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.abstract_cloud_instance.file_structure import INSTANCE_SPOTTY_TMP_DIR, CONTAINERS_TMP_DIR
from spotty.utils import filter_list


VolumeMount = namedtuple('VolumeMount', ['name', 'host_path', 'mount_path', 'mode', 'hidden'])


class AbstractInstanceConfig(ABC):

    def __init__(self, instance_config: dict, project_config: ProjectConfig):
        self._project_config = project_config

        # set instance parameters
        self._name = instance_config['name']
        self._provider_name = instance_config['provider']
        self._params = self._validate_instance_params(instance_config['parameters'])

        # get container config
        container_configs = filter_list(project_config.containers, 'name', self.container_name)
        if not container_configs:
            raise ValueError('Container configuration with the name "%s" not found.' % self.container_name)

        self._container_config = ContainerConfig(container_configs[0])

        # get volumes
        self._volumes = self._get_volumes()

        # get container volume mounts
        self._volume_mounts = self._get_volume_mounts(self._volumes)

        # get the host project directory
        self._host_project_dir = self._get_host_project_dir(self._volume_mounts)

    @abstractmethod
    def _validate_instance_params(self, params: dict) -> dict:
        """Validates instance parameters and fill missing ones with the default values."""
        raise NotImplementedError

    @abstractmethod
    def _get_instance_volumes(self) -> List[AbstractInstanceVolume]:
        """Returns specific to the provider volumes that should be mounted on the host OS."""
        raise NotImplementedError

    @property
    def project_config(self) -> ProjectConfig:
        return self._project_config

    @property
    def container_config(self) -> ContainerConfig:
        return self._container_config

    @property
    @abstractmethod
    def user(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Name of the instance."""
        return self._name

    @property
    def provider_name(self):
        """Provider name."""
        return self._provider_name

    @property
    def container_name(self) -> str:
        return self._params['containerName'] if self._params['containerName'] else DEFAULT_CONTAINER_NAME

    @property
    def full_container_name(self) -> str:
        """A container name that is used in the "docker run" command."""
        return ('spotty-%s-%s-%s' % (self.project_config.project_name, self.name, self.container_name)).lower()

    @property
    def docker_data_root(self) -> str:
        """Data root directory for Docker daemon."""
        return self._params['dockerDataRoot']

    @property
    def local_ssh_port(self) -> int:
        """Local SSH port to connect to the instance (in case of a tunnel)."""
        return self._params['localSshPort']

    @property
    def commands(self) -> str:
        """Commands that should be run once an instance is started."""
        return self._params['commands']

    @property
    def host_project_dir(self):
        """Project directory on the host OS."""
        return self._host_project_dir

    @property
    def volumes(self) -> List[AbstractInstanceVolume]:
        return self._volumes

    @property
    def volume_mounts(self) -> List[VolumeMount]:
        return self._volume_mounts

    @property
    def dockerfile_path(self):
        """Dockerfile path on the host OS."""
        dockerfile_path = self.container_config.file
        if dockerfile_path:
            dockerfile_path = self.host_project_dir + '/' + dockerfile_path

        return dockerfile_path

    @property
    def docker_context_path(self):
        """Docker build's context path on the host OS."""
        dockerfile_path = self.dockerfile_path
        if not dockerfile_path:
            return ''

        return os.path.dirname(dockerfile_path)

    @property
    def host_container_dir(self):
        """A temporary directory on the host OS that contains container-related files and directories."""
        return '%s/%s' % (CONTAINERS_TMP_DIR, self.full_container_name)

    @property
    def host_logs_dir(self):
        """A directory mainly for the "spotty run" command logs."""
        return self.host_container_dir + '/logs'

    @property
    def host_volumes_dir(self):
        """A directory with temporary volumes. If there is a Volume Mount in the configuration file
        that doesn't have a corresponding instance volume, a temporary directory will be created
        and attached to the container.
        """
        return self.host_container_dir + '/volumes'

    def _get_volumes(self) -> List[AbstractInstanceVolume]:
        """Returns volumes that should be mounted on the host OS."""
        volumes = self._get_instance_volumes()

        # create temporary volumes for the volume mounts that don't have corresponding
        # volumes in the instance configuration
        instance_volume_names = set(volume.name for volume in volumes)
        for container_volume in self.container_config.volume_mounts:
            if container_volume['name'] not in instance_volume_names:
                volumes.append(TmpDirVolume(volume_config={
                    'name': container_volume['name'],
                    'parameters': {'path': '%s/%s' % (self.host_volumes_dir, container_volume['name'])}
                }))

        return volumes

    def _get_volume_mounts(self, volumes: List[AbstractInstanceVolume]) \
            -> List[VolumeMount]:
        """Returns container volume mounts and a path to the project directory on the host OS."""
        # get mount directories for the volumes
        host_paths = OrderedDict([(volume.name, volume.host_path) for volume in volumes])

        # get container volumes mapping
        volume_mounts = []
        for container_volume in self.container_config.volume_mounts:
            volume_mounts.append(VolumeMount(
                name=container_volume['name'],
                host_path=host_paths[container_volume['name']],
                mount_path=container_volume['mountPath'],
                mode='rw',
                hidden=False,
            ))

        return volume_mounts

    def _get_host_project_dir(self, volume_mounts: List[VolumeMount]) -> str:
        """Returns the host project directory."""
        host_project_dir = None
        for volume_mount in sorted(volume_mounts, key=lambda x: len(x.mount_path), reverse=True):
            if is_subdir(self.container_config.project_dir, volume_mount.mount_path):
                # the project directory is a subdirectory of a Volume Mount directory
                project_subdir = os.path.relpath(self.container_config.project_dir, volume_mount.mount_path)
                host_project_dir = os.path.normpath(volume_mount.host_path + '/' + project_subdir)
                break

        # this should not be the case as the volume mount for the project directory should be added automatically
        # if it doesn't exist in the configuration
        assert host_project_dir is not None, 'A volume mount that contains the project directory not found.'

        return host_project_dir
