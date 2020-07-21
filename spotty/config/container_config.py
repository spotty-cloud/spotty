from typing import List
from spotty.config.validation import is_subdir


PROJECT_VOLUME_MOUNT_NAME = '.project'


class ContainerConfig(object):

    def __init__(self, container_config: dict):
        self._config = container_config
        self._volume_mounts = self._get_volume_mounts()

    @property
    def name(self) -> str:
        return self._config['name']

    @property
    def project_dir(self) -> str:
        return self._config['projectDir']

    @property
    def image(self) -> str:
        return self._config['image']

    @property
    def file(self) -> str:
        return self._config['file']

    @property
    def run_as_host_user(self) -> str:
        return self._config['runAsHostUser']

    @property
    def volume_mounts(self) -> list:
        return self._volume_mounts

    @property
    def commands(self) -> str:
        return self._config['commands']

    @property
    def working_dir(self) -> str:
        """Working directory for the Docker container."""
        working_dir = self._config['workingDir']
        if not working_dir:
            working_dir = self._config['projectDir']

        return working_dir

    @property
    def env(self) -> dict:
        return self._config['env']

    @property
    def host_network(self) -> bool:
        return self._config['hostNetwork']

    @property
    def ports(self) -> List[dict]:
        return self._config['ports']

    @property
    def runtime_parameters(self) -> list:
        return self._config['runtimeParameters']

    def _get_volume_mounts(self):
        """Returns container volume mounts from the configuration and
        adds the project volume mount if necessary."""

        volume_mounts = self._config['volumeMounts']

        # check if the project directory is a sub-directory of one of the volume mounts
        project_has_volume = False
        for volume_mount in volume_mounts:
            if is_subdir(self.project_dir, volume_mount['mountPath']):
                project_has_volume = True
                break

        # if it's not, then add new volume mount
        if not project_has_volume:
            volume_mounts.insert(0, {
                'name': PROJECT_VOLUME_MOUNT_NAME,
                'mountPath': self.project_dir,
            })

        return volume_mounts
