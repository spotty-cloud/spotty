from abc import ABC


class AbstractInstance(ABC):

    @property
    def public_ip_address(self):
        raise NotImplementedError

    @property
    def is_running(self):
        """Returns true if the instance is running."""
        raise NotImplementedError

    @property
    def is_stopped(self):
        """Returns true if the instance is stopped, so it can be restarted."""
        raise NotImplementedError

    def terminate(self, wait: bool = True):
        raise NotImplementedError

    def stop(self, wait: bool = True):
        raise NotImplementedError
