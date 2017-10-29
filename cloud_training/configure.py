import configparser
import os
from cloud_training import utils


def get_aws_credentials_settings(profile: str = 'default'):
    return get_profile_settings(get_aws_credentials_file_path(), get_aws_profile_name(profile), {
        'aws_access_key_id': None,
        'aws_secret_access_key': None,
    })


def get_aws_config_settings(profile: str = 'default'):
    return get_profile_settings(get_aws_config_file_path(), get_aws_profile_name(profile), {
        'region': None,
    })


def get_ct_settings(profile: str = 'default'):
    return get_profile_settings(get_ct_config_file_path(), profile, {
        's3_bucket': None,
        'image_id': None,
        'root_snapshot_id': None,
        'root_volume_size': None,
        'training_volume_size': 5,
        'key_name': None,
        'instance_type': 'p2.xlarge',
    })


def get_all_settings(profile: str = 'default'):
    return {
        **get_aws_credentials_settings(profile),
        **get_aws_config_settings(profile),
        **get_ct_settings(profile),
    }


def get_aws_credentials_file_path():
    return os.path.join(os.path.expanduser('~'), '.aws', 'credentials')


def get_aws_config_file_path():
    return os.path.join(os.path.expanduser('~'), '.aws', 'config')


def get_ct_config_file_path():
    return os.path.join(os.path.expanduser('~'), '.cloud_training', 'config')


def get_aws_profile_name(profile):
    return 'cloud_training_%s' % profile


def get_profile_settings(filename: str, section: str, defaults: dict):
    config = configparser.ConfigParser()
    config.read(filename)

    settings = dict(defaults)
    if section in config:
        settings = {**settings, **config[section]}

    return settings


def save_profile_settings(filename: str, section: str, settings: dict):
    config = configparser.ConfigParser()
    config.read(filename)
    config[section] = settings

    utils.check_path(os.path.dirname(filename))

    with open(filename, 'w') as f:
        config.write(f)
