from abc import ABC, abstractmethod


class AbstractInstanceVolume(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the volume that will be used for the deployment."""
        raise NotImplementedError

    @property
    @abstractmethod
    def mount_dir(self) -> str:
        """A directory where the volume should be mounted on the host OS."""
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
