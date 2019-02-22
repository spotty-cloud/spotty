from abc import ABC


class AbstractInstanceVolume(ABC):

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def mount_dir(self) -> str:
        raise NotImplementedError

    @property
    def title(self) -> str:
        raise NotImplementedError
