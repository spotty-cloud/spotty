from collections import namedtuple, OrderedDict
import os
from subprocess import list2cmdline
from typing import List
from spotty.config.container_config import ContainerConfig
from spotty.config.validation import is_subdir
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume


VolumeMount = namedtuple('VolumeMount', ['name', 'host_dir', 'container_dir'])


class ContainerDeployment(object):

    def __init__(self, project_name: str, volumes: List[AbstractInstanceVolume], container_config: ContainerConfig):
        self._project_name = project_name
        self._config = container_config

        # get container volumes and host project directory
        self._volume_mounts, self._host_project_dir = self._get_volume_mounts(volumes)

    @property
    def config(self) -> ContainerConfig:
        return self._config

    @property
    def dockerfile_path(self):
        """Dockerfile path on the host OS."""
        dockerfile_path = self.config.file
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
    def host_project_dir(self):
        return self._host_project_dir

    @property
    def volume_mounts(self) -> List[VolumeMount]:
        return self._volume_mounts

    def get_runtime_parameters(self, is_nvidia_runtime: bool):
        """Returns parameters for the ""docker run" command."""
        parameters = self._config.runtime_parameters + ['-td', '--net=host']
        if is_nvidia_runtime:
            parameters += ['--runtime=nvidia']

        for volume_mount in self.volume_mounts:
            parameters += ['-v', '%s:%s' % (volume_mount.host_dir, volume_mount.container_dir)]

        return list2cmdline(parameters)

    def _get_volume_mounts(self, volumes: List[AbstractInstanceVolume]):
        """Get container volume mounts."""
        # get mount directories for the volumes
        mount_dirs = OrderedDict([(volume.name, volume.mount_dir) for volume in volumes])

        # get container volumes mapping
        volume_mounts = []
        for container_volume in self.config.volume_mounts:
            volume_name = container_volume['name']
            host_dir = mount_dirs.get(volume_name, '/tmp/spotty/container/volumes/%s' % volume_name)

            volume_mounts.append(VolumeMount(
                name=volume_name,
                host_dir=host_dir,
                container_dir=container_volume['mountPath'],
            ))

        # get host project directory
        host_project_dir = None
        for name, host_dir, container_dir in volume_mounts:
            if is_subdir(self.config.project_dir, container_dir):
                project_subdir = os.path.relpath(self.config.project_dir, container_dir)
                host_project_dir = host_dir + '/' + project_subdir
                break

        if not host_project_dir:
            # use temporary directory for the project
            host_project_dir = '/tmp/spotty/container/volumes/.project'
            volume_mounts.append(VolumeMount(
                name=None,
                host_dir=host_project_dir,
                container_dir=self.config.project_dir,
            ))

        return volume_mounts, host_project_dir
