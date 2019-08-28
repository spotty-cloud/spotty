import subprocess
from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.gcp.instance_manager import InstanceManager


class CreateImageCommand(AbstractConfigCommand):

    name = 'create-image'
    description = 'Create an image with NVIDIA Docker'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-f', '--family-name', type=str, default=None, help='Set an image family')
        parser.add_argument('--debug-mode', action='store_true', help='Don\'t terminate the instance on failure')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that it's a GCP instance
        if not isinstance(instance_manager, InstanceManager):
            raise ValueError('Instance "%s" is not an GCP instance.' % instance_manager.instance_config.name)

        deployment = instance_manager.image_deployment

        try:
            deployment.deploy(args.family_name, args.debug_mode, output)
        finally:
            if args.debug_mode:
                ip_address = deployment.get_ip_address()
                if ip_address:
                    ssh_command = get_ssh_command(ip_address, instance_manager.ssh_port, instance_manager.ssh_user,
                                                  instance_manager.ssh_key_path, 'tmux')

                    output.write('\nUse the following command to connect to the instance:\n'
                                 '  %s\n' % subprocess.list2cmdline(ssh_command))
