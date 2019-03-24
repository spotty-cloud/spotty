from abc import ABC, abstractmethod
from contextlib import contextmanager


class AbstractOutputWriter(ABC):

    def __init__(self):
        self._prefix = ''

    @abstractmethod
    def _write(self, msg: str):
        raise NotImplementedError

    def write(self, msg: str = ''):
        msg = '\n'.join([self._prefix + line for line in msg.split('\n')])
        self._write(msg)

    @contextmanager
    def prefix(self, prefix):
        self._prefix += prefix
        yield
        self._prefix = self._prefix[:-len(prefix)]
