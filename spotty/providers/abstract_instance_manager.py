from abc import ABC, abstractmethod
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.project_config import ProjectConfig


class AbstractInstanceManager(ABC):

    def __init__(self, instance_config: dict, project_config: ProjectConfig):
        self._instance_config = instance_config
        self._project_config = project_config

    @property
    def project_config(self) -> ProjectConfig:
        return self._project_config

    @property
    def instance_config(self) -> dict:
        return self._instance_config

    @abstractmethod
    def is_running(self):
        """Checks if the instance is running."""
        raise NotImplementedError

    @abstractmethod
    def start(self, output: AbstractOutputWriter, dry_run=False):
        """Creates a stack with the instance."""
        raise NotImplementedError

    @abstractmethod
    def stop(self, output: AbstractOutputWriter):
        """Deletes the stack."""
        raise NotImplementedError

    @abstractmethod
    def clean(self, output: AbstractOutputWriter):
        """Deletes the stack."""
        raise NotImplementedError

    @abstractmethod
    def sync(self, output: AbstractOutputWriter, dry_run=False):
        """Synchronizes the project code with the instance."""
        raise NotImplementedError

    @property
    def status_text(self):
        """Information about the running instance that will be
        shown to the user once the instance is started or the "status"
        command is called.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def ip_address(self):
        """Returns an IP address of the running instance."""
        raise NotImplementedError

    @property
    @abstractmethod
    def ssh_user(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def ssh_key_path(self):
        raise NotImplementedError

    @property
    def local_ssh_port(self) -> int:
        # TODO: add the check to the general config validator
        return self._instance_config['parameters']['localSshPort']
