from abc import ABC
from spotty.deployment.container_commands.docker_commands import DockerCommands
from spotty.deployment.container_scripts.abstract_container_script import AbstractContainerScript


class AbstractDockerScript(AbstractContainerScript, ABC):

    def __init__(self, container_commands: DockerCommands):
        super().__init__(container_commands)

    @property
    def commands(self) -> DockerCommands:
        return self._commands
