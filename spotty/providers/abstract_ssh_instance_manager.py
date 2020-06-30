from abc import abstractmethod
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.commands import get_ssh_command, get_script_command
from spotty.deployment.docker.docker_commands import DockerCommands
from spotty.deployment.docker.scripts.start_container_script import StartContainerScript
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class AbstractSshInstanceManager(AbstractInstanceManager):

    @property
    def container_commands(self) -> DockerCommands:
        """A collection of commands to manage a container from the host OS."""
        return DockerCommands(self.instance_config)

    def start_container(self, output: AbstractOutputWriter, dry_run=False):
        """Starts or restarts container on the host OS."""
        start_container_script = StartContainerScript(self.container_commands).render()
        start_container_command = get_script_command('start-container', start_container_script)

        exit_code = self.exec(start_container_command)
        if exit_code != 0:
            raise ValueError('Failed to start the container')

    def exec(self, command: str) -> int:
        """Executes a command on the host OS."""
        ssh_command = get_ssh_command(self.get_ip_address(), self.ssh_port, self.ssh_user, self.ssh_key_path,
                                      command, env_vars=self.ssh_env_vars)

        return super().exec(ssh_command)

    @abstractmethod
    def get_public_ip_address(self) -> str:
        """Returns a public IP address of the running instance."""
        raise NotImplementedError

    def get_ip_address(self):
        """Returns an IP address that will be used for SSH connections."""
        if self._instance_config.local_ssh_port:
            return '127.0.0.1'

        public_ip_address = self.get_public_ip_address()
        if not public_ip_address:
            raise ValueError('The running instance doesn\'t have a public IP address.\n'
                             'Use the "localSshPort" parameter if you want to create a tunnel to the instance.')

        return public_ip_address

    @property
    def ssh_port(self) -> int:
        if self._instance_config.local_ssh_port:
            return self._instance_config.local_ssh_port

        return 22

    @property
    @abstractmethod
    def ssh_user(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def ssh_key_path(self) -> str:
        raise NotImplementedError

    @property
    def ssh_env_vars(self) -> dict:
        """Environmental variables that will be set when ssh to the instance."""
        return {
            'SPOTTY_CONTAINER_NAME': self.instance_config.full_container_name,
            'SPOTTY_CONTAINER_WORKING_DIR': self.instance_config.container_config.working_dir,
        }

    @property
    def use_tmux(self) -> bool:
        return True
