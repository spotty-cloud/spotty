from abc import ABC, abstractmethod


class AbstractInstanceVolume(ABC):

    def __init__(self, volume_config: dict):
        self._name = volume_config['name']
        self._params = self._validate_volume_parameters(volume_config['parameters'])

    @abstractmethod
    def _validate_volume_parameters(self, params: dict) -> dict:
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Unique name of the volume that will be used for the deployment."""
        return self._name

    @property
    @abstractmethod
    def host_path(self) -> str:
        """A path on the host OS that will be mounted to the container."""
        raise NotImplementedError

    @property
    @abstractmethod
    def title(self) -> str:
        """A title for the volume type.
        It will be used to display information about the volumes during the deployment.
        """
        raise NotImplementedError

    @property
    def deletion_policy_title(self) -> str:
        """A title for the volume's deletion policy.
        It will be used to display information about the volumes during the deployment.
        """
        return ''
