from abc import ABC, abstractmethod
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class AbstractInstanceManager(ABC):

    def __init__(self, project_name: str, instance_name: str, instance_params: dict, container_config: dict):
        self._project_name = project_name
        self._instance_name = instance_name
        self._instance_params = instance_params
        self._container_config = container_config

    @property
    def instance_name(self):
        return self._instance_name

    @abstractmethod
    def is_running(self):
        """Checks if the instance is running."""
        raise NotImplementedError

    @abstractmethod
    def start(self, project_dir: str, sync_filters: list, output: AbstractOutputWriter, dry_run=False):
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
    def sync(self, project_dir: str, sync_filters: list, output: AbstractOutputWriter, dry_run=False):
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
    @abstractmethod
    def local_ssh_port(self):
        raise NotImplementedError
