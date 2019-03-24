from argparse import Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class StopCommand(AbstractConfigCommand):

    name = 'stop'
    description = 'Terminate running instance and apply deletion policies for the volumes'

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):

        instance_manager.stop(output)

        output.write('\n'
                     '----------------------------------\n'
                     'Instance was successfully deleted.\n'
                     '----------------------------------')
