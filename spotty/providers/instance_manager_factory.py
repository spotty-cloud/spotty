from importlib import import_module
from spotty.config.project_config import ProjectConfig
from spotty.deployment.abstract_instance_manager import AbstractInstanceManager


PROVIDER_AWS = 'aws'
PROVIDER_GCP = 'gcp'
PROVIDER_LOCAL = 'local'
PROVIDER_REMOTE = 'remote'


class InstanceManagerFactory(object):

    SUPPORTED_PROVIDERS = [
        PROVIDER_AWS,
        PROVIDER_GCP,
        PROVIDER_LOCAL,
        PROVIDER_REMOTE,
    ]

    @classmethod
    def get_instance(cls, project_config: ProjectConfig, instance_config: dict) -> AbstractInstanceManager:
        provider_name = instance_config['provider']
        if provider_name not in cls.SUPPORTED_PROVIDERS:
            raise ValueError('Provider "%s" is not supported' % provider_name)

        # get Instance Manger class for the provider
        InstanceManagerClass = getattr(import_module('spotty.providers.%s.instance_manager' % provider_name),
                                       'InstanceManager')

        return InstanceManagerClass(project_config, instance_config)
