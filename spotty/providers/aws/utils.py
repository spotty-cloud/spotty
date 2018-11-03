import os


def data_dir(path: str = ''):
    """Returns an absolute path to the data directory for AWS provider.

    Args:
        path: A relative path to add to the package path.

    """
    res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if path:
        res_path = os.path.join(res_path, path)

    return res_path
