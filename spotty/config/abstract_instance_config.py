import os
from abc import ABC, abstractmethod
from collections import OrderedDict, namedtuple
from typing import List
from spotty.config.container_config import ContainerConfig
from spotty.config.project_config import ProjectConfig
from spotty.config.validation import DEFAULT_CONTAINER_NAME, is_subdir
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.file_structure import INSTANCE_SPOTTY_TMP_DIR
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
            raise ValueError('Container configuration for the instance not found.')

        self._container_config = ContainerConfig(container_configs[0])

        # get container volume mounts and a host project directory
        self._volume_mounts, self._host_project_dir = self._get_volume_mounts()

    @abstractmethod
    def _validate_instance_params(self, params: dict) -> dict:
        """Validates instance parameters and fill missing ones with the default values."""
        raise NotImplementedError

    @property
    def project_config(self) -> ProjectConfig:
        return self._project_config

    @property
    def container_config(self) -> ContainerConfig:
        return self._container_config

    @property
    @abstractmethod
    def volumes(self) -> List[AbstractInstanceVolume]:
        """List of volume configs."""
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
        return 'spotty-%s-%s' % (self.project_config.project_name, self.container_name)

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
    def env_vars(self) -> dict:
        """Environmental variables that will be set when ssh to the instance."""
        return {
            'SPOTTY_CONTAINER_NAME': self.full_container_name if self.container_config else '',
            'SPOTTY_CONTAINER_WORKING_DIR': self.container_config.working_dir if self.container_config else '',
        }

    @property
    def host_project_dir(self):
        """Project directory on the host OS."""
        return self._host_project_dir

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
        return '%s/containers/%s' % (INSTANCE_SPOTTY_TMP_DIR, self.full_container_name)

    @property
    def host_scripts_dir(self):
        """A directory with scripts that will be run inside a container."""
        return self.host_container_dir + '/scripts'

    @property
    def host_logs_dir(self):
        """A directory mainly for the "spotty run" command logs."""
        return self.host_container_dir + '/logs'

    @property
    def host_run_scripts_dir(self):
        """A directory with custom user scripts (the "spotty run" command)."""
        return self.host_scripts_dir + '/run'

    @property
    def host_volumes_dir(self):
        """A directory with temporary volumes. If there is a Volume Mount in the configuration file
        that doesn't have a corresponding instance volume, a temporary directory will be created
        and attached to the container.
        """
        return self.host_container_dir + '/volumes'

    def _get_volume_mounts(self) -> (List[VolumeMount], str):
        """Returns container volume mounts and a path to the project directory on the host OS."""
        # get mount directories for the volumes
        host_paths = OrderedDict([(volume.name, volume.host_path) for volume in self.volumes])

        # get container volumes mapping
        volume_mounts = []
        for container_volume in self.container_config.volume_mounts:
            volume_name = container_volume['name']
            host_path = host_paths.get(volume_name, '%s/%s' % (self.host_volumes_dir, volume_name))

            volume_mounts.append(VolumeMount(
                name=volume_name,
                host_path=host_path,
                mount_path=container_volume['mountPath'],
                mode='rw',
                hidden=False,
            ))

        # get host project directory
        host_project_dir = None
        for _, host_path, mount_path, _, _ in volume_mounts:
            if is_subdir(self.container_config.project_dir, mount_path):
                # the project directory is a subdirectory of a Volume Mount directory
                project_subdir = os.path.relpath(self.container_config.project_dir, mount_path)
                host_project_dir = os.path.normpath(host_path + '/' + project_subdir)
                break

        if not host_project_dir:
            # use temporary directory for the project
            host_project_dir = self.host_volumes_dir + '/.project'
            volume_mounts.append(VolumeMount(
                name=None,
                host_path=host_project_dir,
                mount_path=self.container_config.project_dir,
                mode='rw',
                hidden=False,
            ))

        return volume_mounts, host_project_dir
