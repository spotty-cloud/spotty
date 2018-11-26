from abc import ABC, abstractmethod


class AbstractVolumeConfig(ABC):

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def mount_dir(self):
        raise NotImplementedError
