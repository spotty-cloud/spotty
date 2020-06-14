from typing import List


class ContainerConfig(object):

    def __init__(self, container_config: dict):
        self._config = container_config

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
    def volume_mounts(self) -> list:
        return self._config['volumeMounts']

    @property
    def ports(self) -> List[int]:
        return list(set(self._config['ports']))

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
    def runtime_parameters(self) -> list:
        return self._config['runtimeParameters']
