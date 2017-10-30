from abc import ABC, abstractmethod
from argparse import Namespace
from cloud_training import configure


class AbstractCommand(ABC):

    """Abstract class for implementing a command"""

    def __init__(self, args: Namespace):
        """Command's constructor

        Args:
            args: arguments provided by argparse.

        Raises:
            ValueError: If command's arguments can't be processed.

        """
        self._args = args
        self._settings = configure.get_all_settings(self._args.profile)

    @abstractmethod
    def run(self) -> bool:
        """Performs a command

        Returns:
            bool: True for success, False otherwise.

        Raises:
            ValueError: If command's arguments can't be processed.
        """
        return True

    def _print(self, message):
        """Print results to the console."""
        print(message, flush=True)
