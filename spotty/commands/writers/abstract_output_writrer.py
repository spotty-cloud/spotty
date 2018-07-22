from abc import ABC, abstractmethod


class AbstractOutputWriter(ABC):

    @abstractmethod
    def write(self, msg: str):
        pass
