import os
import yaml
from spotty.config.project_config import ProjectConfig


DEFAULT_CONFIG_FILENAME = 'spotty.yaml'
OVERRIDE_CONFIG_FILENAME = 'spotty.override.yaml'


def load_config(config_path: str = None) -> ProjectConfig:
    # get project directory
    if not config_path:
        config_path = DEFAULT_CONFIG_FILENAME

    if os.path.isabs(config_path):
        config_abs_path = config_path
    else:
        config_abs_path = os.path.abspath(os.path.join(os.getcwd(), config_path))

    if not os.path.exists(config_abs_path):
        raise ValueError('Configuration file "%s" not found.' % config_path)

    # get the project directory
    project_dir = os.path.dirname(config_abs_path)

    # read the config
    config = _read_yaml(config_abs_path)

    # update the config if an override config exists
    if os.path.basename(config_abs_path) == DEFAULT_CONFIG_FILENAME:
        override_config_abs_path = os.path.join(project_dir, OVERRIDE_CONFIG_FILENAME)
        if os.path.isfile(override_config_abs_path):
            override_config = _read_yaml(override_config_abs_path)
            config = _update_dict(config, override_config)

    # get project configuration
    project_config = ProjectConfig(config, project_dir)

    return project_config


def _read_yaml(file_path: str):
    """Returns content of the YAML file."""
    with open(file_path, 'r') as f:
        res = yaml.safe_load(f)

    return res


def _update_dict(d, u):
    if not isinstance(u, dict):
        return d

    if not isinstance(d, dict):
        return u

    for k, v in u.items():
        if isinstance(d, dict):
            if isinstance(v, dict):
                d[k] = _update_dict(d.get(k, {}), v)
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}

    return d
