from abc import abstractmethod, ABC
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.abstract_instance_config import AbstractInstanceConfig
from spotty.deployment.abstract_cloud_instance.abstract_data_transfer import AbstractDataTransfer
from spotty.deployment.abstract_cloud_instance.resources.abstract_instance import AbstractInstance
from spotty.deployment.container.abstract_container_commands import AbstractContainerCommands


class AbstractInstanceDeployment(ABC):

    def __init__(self, instance_config: AbstractInstanceConfig):
        self._instance_config = instance_config

    @property
    def instance_config(self) -> AbstractInstanceConfig:
        return self._instance_config

    @abstractmethod
    def get_instance(self) -> AbstractInstance:
        """Returns information about the instance it it exists."""
        raise NotImplementedError

    @abstractmethod
    def deploy(self, container_commands: AbstractContainerCommands, bucket_name: str,
               data_transfer: AbstractDataTransfer, output: AbstractOutputWriter, dry_run: bool = False):
        """Deploys or redeploys the instance."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, output: AbstractOutputWriter):
        """Deletes the stack with the instance and applies deletion policies for the volumes."""
        raise NotImplementedError
