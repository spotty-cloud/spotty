from abc import ABC


class AbstractBucket(ABC):

    @property
    def name(self):
        raise NotImplementedError
