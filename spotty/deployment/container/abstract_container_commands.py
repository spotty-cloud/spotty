from abc import ABC, abstractmethod
from spotty.config.abstract_instance_config import AbstractInstanceConfig


class AbstractContainerCommands(ABC):

    def __init__(self, instance_config: AbstractInstanceConfig):
        self._instance_config = instance_config

    @property
    def instance_config(self) -> AbstractInstanceConfig:
        return self._instance_config

    @abstractmethod
    def exec(self, command: str, interactive: bool = False, tty: bool = False, user: str = None,
             container_name: str = None, working_dir: str = None) -> str:
        raise NotImplementedError
