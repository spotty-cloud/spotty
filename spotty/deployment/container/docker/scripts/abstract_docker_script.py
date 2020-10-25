from abc import ABC
from spotty.deployment.container.docker.docker_commands import DockerCommands
from spotty.deployment.container.abstract_container_script import AbstractContainerScript


class AbstractDockerScript(AbstractContainerScript, ABC):

    @property
    def commands(self) -> DockerCommands:
        return self._commands
