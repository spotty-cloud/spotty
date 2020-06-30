from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.commands import get_script_command
from spotty.deployment.docker.docker_commands import DockerCommands
from spotty.deployment.docker.scripts.start_container_script import StartContainerScript
from spotty.deployment.docker.scripts.stop_container_script import StopContainerScript
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.providers.local.config.instance_config import InstanceConfig
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class InstanceManager(AbstractInstanceManager):

    instance_config: InstanceConfig

    def _get_instance_config(self, instance_config: dict) -> InstanceConfig:
        """Validates the instance config and returns an InstanceConfig object."""
        return InstanceConfig(instance_config, self.project_config)

    @property
    def container_commands(self) -> DockerCommands:
        """A collection of commands to manage a container from the host OS."""
        return DockerCommands(self.instance_config)

    def is_running(self):
        """It's this instance, so it's running."""
        return True

    def start(self, output: AbstractOutputWriter, dry_run=False):
        # start or restart container
        self.start_container(output, dry_run=dry_run)

    def start_container(self, output: AbstractOutputWriter, dry_run=False):
        """Starts or restarts container on the host OS."""
        start_container_script = StartContainerScript(self.container_commands).render()
        start_container_command = get_script_command('start-container', start_container_script)

        exit_code = self.exec(start_container_command)
        if exit_code != 0:
            raise ValueError('Failed to start the container')

    def stop(self, only_shutdown: bool, output: AbstractOutputWriter):
        # stop container
        stop_container_script = StopContainerScript(self.container_commands).render()
        stop_container_command = get_script_command('stop-container', stop_container_script)

        exit_code = self.exec(stop_container_command)
        if exit_code != 0:
            raise ValueError('Failed to stop the container')

    def clean(self, output: AbstractOutputWriter):
        pass

    def sync(self, output: AbstractOutputWriter, dry_run=False):
        raise NothingToDoError('Nothing to do. The project directory is mounted to the container.')

    def download(self, download_filters: list, output: AbstractOutputWriter, dry_run=False):
        raise NothingToDoError('Nothing to do. The project directory is mounted to the container.')

    def get_status_text(self):
        if self.is_running():
            msg = 'Container is running.'
        else:
            msg = 'Container is not running.'

        return msg
