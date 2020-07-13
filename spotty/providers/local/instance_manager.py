from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.deployment.abstract_docker_instance_manager import AbstractDockerInstanceManager
from spotty.providers.local.config.instance_config import InstanceConfig


class InstanceManager(AbstractDockerInstanceManager):

    instance_config: InstanceConfig

    def _get_instance_config(self, instance_config: dict) -> InstanceConfig:
        """Validates the instance config and returns an InstanceConfig object."""
        return InstanceConfig(instance_config, self.project_config)

    def is_running(self):
        return True

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        raise NothingToDoError('Nothing to do. The project directory is mounted to the container.')

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):
        raise NothingToDoError('Nothing to do. The project directory is mounted to the container.')
