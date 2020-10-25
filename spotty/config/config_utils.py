import os
from collections import namedtuple
import yaml
from spotty.config.project_config import ProjectConfig
from spotty.config.validation import DEFAULT_CONTAINER_NAME


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
            config = _merge_configs(config, override_config)

    # get project configuration
    project_config = ProjectConfig(config, project_dir)

    return project_config


def _read_yaml(file_path: str):
    """Returns content of the YAML file."""
    with open(file_path, 'r') as f:
        res = yaml.safe_load(f)

    return res


def _merge_configs(orig_config, override_config):
    """Merges original config with the override config."""

    MergeRule = namedtuple('MergeRule', ['key', 'merge_key', 'default_value', 'has_default_value'])

    merge_rules = [MergeRule(
        key='containers',
        merge_key='name',
        default_value=DEFAULT_CONTAINER_NAME,
        has_default_value=True,
    ), MergeRule(
        key='instances',
        merge_key='name',
        default_value=None,
        has_default_value=False,
    )]

    # validate and merge lists by keys
    for rule in merge_rules:
        if override_config and (rule.key in orig_config) and (rule.key in override_config):
            if not isinstance(orig_config[rule.key], list):
                raise ValueError('The "%s" key in the config must be a list.' % rule.key)

            if not isinstance(override_config[rule.key], list):
                raise ValueError('The "%s" key in the override config must be a list.' % rule.key)

            # convert lists to dictionaries
            dicts_to_merge = []
            for list_to_merge in [orig_config[rule.key], override_config[rule.key]]:
                dict_to_merge = {}
                for item in list_to_merge:
                    if not isinstance(item, dict):
                        raise ValueError('Each item of the "%s" list must be a dictionary.' % rule.key)

                    if rule.merge_key in item:
                        merge_value = item[rule.merge_key]
                    elif rule.has_default_value:
                        merge_value = rule.default_value
                    else:
                        raise ValueError('Each item of the "%s" list must contain the "%s" field.'
                                         % (rule.key, rule.merge_key))

                    if merge_value in dict_to_merge:
                        raise ValueError('Each item of the "%s" list must have a unique "%s" value.'
                                         % (rule.key, rule.merge_key))

                    dict_to_merge[merge_value] = item

                dicts_to_merge.append(dict_to_merge)

            # merge lists
            merged_dict = _update_dict(*dicts_to_merge)
            orig_config[rule.key] = [{**item, rule.merge_key: key} for key, item in merged_dict.items()]
            del override_config[rule.key]

    # merge the rest of the override config
    config = _update_dict(orig_config, override_config)

    return config


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
