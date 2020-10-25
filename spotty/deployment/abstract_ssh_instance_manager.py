import logging
import os
from abc import abstractmethod
from spotty.deployment.utils.commands import get_ssh_command
from spotty.deployment.abstract_docker_instance_manager import AbstractDockerInstanceManager


class AbstractSshInstanceManager(AbstractDockerInstanceManager):

    def exec(self, command: str, tty: bool = True) -> int:
        """Executes a command on the host OS."""
        if not os.path.isfile(self.ssh_key_path):
            raise ValueError('SSH key doesn\'t exist: ' + self.ssh_key_path)

        ssh_command = get_ssh_command(self.ssh_host, self.ssh_port, self.ssh_user, self.ssh_key_path,
                                      command, env_vars=self.ssh_env_vars, tty=tty)
        logging.debug('SSH command: ' + ssh_command)

        return super().exec(ssh_command)

    @property
    @abstractmethod
    def ssh_host(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def ssh_port(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def ssh_key_path(self) -> str:
        raise NotImplementedError

    @property
    def ssh_user(self) -> str:
        return self.instance_config.user

    @property
    def ssh_env_vars(self) -> dict:
        """Environmental variables that will be set when ssh to the instance."""
        return {
            'SPOTTY_CONTAINER_NAME': self.instance_config.full_container_name,
            'SPOTTY_CONTAINER_WORKING_DIR': self.instance_config.container_config.working_dir,
        }

    @property
    def use_tmux(self) -> bool:
        """Use tmux when running a custom script or connecting to the instance."""
        return True
