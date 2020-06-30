from abc import ABC


class AbstractInstance(ABC):

    @property
    def public_ip_address(self):
        raise NotImplementedError

    @property
    def is_running(self):
        raise NotImplementedError

    @property
    def is_stopped(self):
        raise NotImplementedError

    def terminate(self, wait: bool = True):
        raise NotImplementedError

    def stop(self, wait: bool = True):
        raise NotImplementedError
