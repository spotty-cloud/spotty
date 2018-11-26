from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.aws.instance_manager import AwsInstanceManager
from spotty.providers.aws.validation import is_gpu_instance
from spotty.providers.aws.project_resources.ami_stack import AmiStackResource


class CreateAmiCommand(AbstractConfigCommand):

    name = 'create-ami'
    description = 'Create AMI with NVIDIA Docker'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-k', '--key-name', type=str, default=None, help='EC2 Key Pair name')

    def _run(self, project_dir: str, config: dict, instance_manager: AbstractInstanceManager,
             args: Namespace, output: AbstractOutputWriter):
        key_name = args.key_name

        # check that it's an AWS instance
        if not isinstance(instance_manager, AwsInstanceManager):
            raise ValueError('Instance "%s" is not an AWS instance.' % instance_manager.instance_name)

        # check that it's a GPU instance type
        instance_type = instance_manager.config.instance_type
        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        # check that an image with this name doesn't exist yet
        ami = instance_manager.config.get_ami()
        if ami:
            raise ValueError('AMI with name "%s" already exists.' % ami.name)

        # check availability zone and subnet
        instance_manager.config.check_az_and_subnet()

        ami_stack = AmiStackResource(instance_manager.config.region)

        # prepare CF template
        availability_zone = instance_manager.config.availability_zone
        subnet_id = instance_manager.config.subnet_id
        on_demand = instance_manager.config.on_demand
        template = ami_stack.prepare_template(availability_zone, subnet_id, key_name, on_demand)

        # create stack
        ami_name = instance_manager.config.ami_name
        ami_stack.create_stack(template, instance_type, ami_name, key_name, output)
