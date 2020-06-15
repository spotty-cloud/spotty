from argparse import Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.errors.instance_not_running import InstanceNotRunningError
from spotty.providers.abstract_instance_manager import AbstractInstanceManager
from spotty.providers.aws.instance_manager import InstanceManager


class StartContainerCommand(AbstractConfigCommand):

    name = 'start-container'
    description = 'Starts or restarts a Docker container on the running instance'

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):
        # check that it's an AWS instance
        if not isinstance(instance_manager, InstanceManager):
            raise ValueError('Instance "%s" is not an AWS instance.' % instance_manager.instance_config.name)

        # check that the instance is started
        if not instance_manager.is_running():
            raise InstanceNotRunningError(instance_manager.instance_config.name)

        instance_manager.start_container(output)
        output.write('Done')
