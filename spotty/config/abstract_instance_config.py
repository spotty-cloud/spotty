from abc import ABC


class AbstractInstanceConfig(ABC):

    def __init__(self, config: dict):
        self._name = config['name']
        self._params = config['parameters']

    @property
    def name(self) -> str:
        """Name of the instance."""
        return self._name

    @property
    def volumes(self) -> list:
        """List of volume configs."""
        return self._params['volumes']

    @property
    def docker_data_root(self) -> str:
        """Data root directory for Docker daemon."""
        return self._params['dockerDataRoot']

    @property
    def local_ssh_port(self) -> int:
        """Local SSH port to connect to the instance (in case of a tunnel)."""
        return self._params['localSshPort']
