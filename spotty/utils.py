import os
import random
import string
import errno


def package_dir(path: str = ''):
    """Returns an absolute path to the "spotty" package directory.

    Args:
        path: A relative path to add to the package path.

    """
    res_path = os.path.dirname(os.path.abspath(__file__))
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


def filter_list(list_of_dicts, key_name, value):
    return [row for row in list_of_dicts if row[key_name] == value]
