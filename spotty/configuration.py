import os


def get_spotty_config_dir():
    """Spotty configuration directory."""
    path = os.path.join(os.path.expanduser('~'), '.spotty')
    if not os.path.isdir(path):
        os.makedirs(path, mode=0o755, exist_ok=True)

    return path


def get_spotty_keys_dir(provider_name: str):
    """"Spotty keys directory."""
    path = os.path.join(get_spotty_config_dir(), 'keys', provider_name)
    if not os.path.isdir(path):
        os.makedirs(path, mode=0o755, exist_ok=True)

    return path
