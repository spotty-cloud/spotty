from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.gcp.deployment.image_deployment import ImageDeployment
from spotty.providers.gcp.instance_manager import InstanceManager


class CreateImageCommand(AbstractConfigCommand):

    name = 'create-image'
    description = 'Create an image with NVIDIA Docker'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-k', '--key-name', type=str, default=None, help='EC2 Key Pair name')
        parser.add_argument('--keep-instance', action='store_true', help='Don\'t terminate the instance on failure')
        parser.add_argument('--dry-run', action='store_true', help='Displays the steps that would be performed '
                                                                   'using the specified command without actually '
                                                                   'running them')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that it's a GCP instance
        if not isinstance(instance_manager, InstanceManager):
            raise ValueError('Instance "%s" is not an GCP instance.' % instance_manager.instance_config.name)

        image_deployment = ImageDeployment(instance_manager.instance_config)
        image_deployment.deploy(args.key_name, args.keep_instance, output, args.dry_run)
