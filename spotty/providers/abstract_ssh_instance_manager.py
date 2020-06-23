from abc import abstractmethod
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
import subprocess


class AbstractSshInstanceManager(AbstractInstanceManager):

    def exec(self, command: list):
        """Executes a command on the host OS."""
        ssh_command = get_ssh_command(self.get_ip_address(), self.ssh_port, self.ssh_user, self.ssh_key_path,
                                      command, env_vars=self.instance_config.env_vars)
        subprocess.call(ssh_command)

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
