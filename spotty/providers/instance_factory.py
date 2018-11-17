from importlib import import_module
from spotty.providers.abstract_instance import AbstractInstance


class InstanceFactory(object):

    INSTANCE_CLASSES = {
        'aws': 'AwsInstance',
    }

    @classmethod
    def get_instance(cls, project_name: str, instance_config: dict) -> AbstractInstance:
        provider_name = instance_config['provider']
        if provider_name not in cls.INSTANCE_CLASSES:
            raise ValueError('Provider "%s" is not supported' % provider_name)

        InstanceClass = getattr(import_module('spotty.providers.%s.instance' % provider_name),
                                cls.INSTANCE_CLASSES[provider_name])

        return InstanceClass(project_name, instance_config)
