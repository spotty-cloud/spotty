from subprocess import list2cmdline
from spotty.config.abstract_instance_config import AbstractInstanceConfig


class ContainerDeployment(object):

    def __init__(self, instance_config: AbstractInstanceConfig):
        self._instance_config = instance_config

    def get_runtime_parameters(self):
        """Returns parameters for the ""docker run" command."""
        parameters = self._instance_config.container_config.runtime_parameters

        for volume_mount in self._instance_config.volume_mounts:
            parameters += ['-v', '%s:%s' % (volume_mount.host_path, volume_mount.mount_path)]

        return list2cmdline(parameters)
