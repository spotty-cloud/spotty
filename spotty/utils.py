import os
import random
import string
import errno


def data_dir(path: str = ''):
    """Returns an absolute path to "data" directory.

    Args:
        path: A path which should be added to the "data" path.

    """
    res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if path:
        res_path = os.path.join(res_path, path)

    return res_path


def check_path(path):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise


def random_string(length: int, chars: str = string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))
