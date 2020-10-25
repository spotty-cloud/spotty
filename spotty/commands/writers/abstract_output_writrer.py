from abc import ABC, abstractmethod
from contextlib import contextmanager


class AbstractOutputWriter(ABC):

    def __init__(self):
        self._prefix = ''
        self._ignore_prefix = False

    @abstractmethod
    def _write(self, msg: str, newline: bool = True):
        raise NotImplementedError

    def write(self, msg: str = '', newline: bool = True):
        if not self._ignore_prefix:
            msg = '\n'.join([self._prefix + line for line in msg.split('\n')])

        self._write(msg, newline=newline)
        self._ignore_prefix = not newline

    @contextmanager
    def prefix(self, prefix):
        self._prefix += prefix
        yield
        self._prefix = self._prefix[:-len(prefix)]
