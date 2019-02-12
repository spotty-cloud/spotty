from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.aws.deployment.ami_deployment import AmiDeployment
from spotty.providers.aws.instance_manager import InstanceManager


class CreateAmiCommand(AbstractConfigCommand):

    name = 'create-ami'
    description = 'Create AMI with NVIDIA Docker'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--debug-mode', action='store_true', help='Don\'t terminate the instance on failure')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that it's an AWS instance
        if not isinstance(instance_manager, InstanceManager):
            raise ValueError('Instance "%s" is not an AWS instance.' % instance_manager.instance_config.instance_name)

        deployment = AmiDeployment(instance_manager.project_config.project_name, instance_manager.instance_config)
        deployment.deploy(args.debug_mode, output)
