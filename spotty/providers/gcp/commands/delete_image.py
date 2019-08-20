from argparse import Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.gcp.instance_manager import InstanceManager


class DeleteImageCommand(AbstractConfigCommand):

    name = 'delete-image'
    description = 'Delete an image with NVIDIA Docker'

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that it's an AWS instance
        if not isinstance(instance_manager, InstanceManager):
            raise ValueError('Instance "%s" is not an AWS instance.' % instance_manager.instance_config.name)

        instance_manager.image_deployment.delete(output)
