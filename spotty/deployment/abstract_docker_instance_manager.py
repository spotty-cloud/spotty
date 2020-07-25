import os
from abc import ABC
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.utils.commands import get_script_command
from spotty.deployment.container.docker.docker_commands import DockerCommands
from spotty.deployment.container.docker.scripts.start_container_script import StartContainerScript
from spotty.deployment.container.docker.scripts.stop_container_script import StopContainerScript
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager
from spotty.errors.nothing_to_do import NothingToDoError
from spotty.utils import render_table


class AbstractDockerInstanceManager(AbstractInstanceManager, ABC):

    @property
    def container_commands(self) -> DockerCommands:
        """A collection of commands to manage a container from the host OS."""
        return DockerCommands(self.instance_config)

    def is_container_running(self) -> bool:
        """Checks if the container is running."""
        is_running_cmd = self.container_commands.is_created(is_running=True)
        exit_code = self.exec(is_running_cmd)

        return exit_code == 0

    def start_container(self, output: AbstractOutputWriter, dry_run=False):
        """Starts or restarts container on the host OS."""
        # make sure the Dockerfile exists
        self._check_dockerfile_exists()

        # sync the project with the instance
        try:
            self.sync(output, dry_run=dry_run)
        except NothingToDoError:
            pass

        # generate a script that starts container
        start_container_script = StartContainerScript(self.container_commands).render()
        start_container_command = get_script_command('start-container', start_container_script)

        # start the container
        exit_code = self.exec(start_container_command)
        if exit_code != 0:
            raise ValueError('Failed to start the container')

    def start(self, output: AbstractOutputWriter, dry_run=False):
        # start or restart container
        self.start_container(output, dry_run=dry_run)

    def stop(self, only_shutdown: bool, output: AbstractOutputWriter):
        # stop container
        stop_container_script = StopContainerScript(self.container_commands).render()
        stop_container_command = get_script_command('stop-container', stop_container_script)

        exit_code = self.exec(stop_container_command)
        if exit_code != 0:
            raise ValueError('Failed to stop the container')

    def get_status_text(self):
        if self.is_container_running():
            msg = 'Container is running.'
        else:
            msg = 'Container is not running.'

        return render_table([(msg,)])

    def _check_dockerfile_exists(self):
        """Raises an error if a Dockerfile specified in the configuration file but doesn't exist."""
        if self.instance_config.container_config.file:
            dockerfile_path = os.path.join(self.project_config.project_dir, self.instance_config.container_config.file)
            if not os.path.isfile(dockerfile_path):
                raise FileNotFoundError('A Dockerfile specified in the container configuration doesn\'t exist:\n  ' +
                                        dockerfile_path)
