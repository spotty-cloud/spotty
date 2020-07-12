from abc import ABC, abstractmethod
from spotty.deployment.container.abstract_container_commands import AbstractContainerCommands


class AbstractContainerScript(ABC):

    def __init__(self, container_commands: AbstractContainerCommands):
        self._commands = container_commands

    @property
    def commands(self) -> AbstractContainerCommands:
        return self._commands

    @abstractmethod
    def render(self) -> str:
        raise NotImplementedError
