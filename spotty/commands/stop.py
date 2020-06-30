from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.abstract_instance_manager import AbstractInstanceManager


class StopCommand(AbstractConfigCommand):

    name = 'stop'
    description = 'Terminate running instance and apply deletion policies for the volumes'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-s', '--shutdown', action='store_true',
                            help='Shutdown the instance without terminating it. Deletion policies for the volumes '
                                 'won\'t be applied.')

    def _run(self, instance_manager: AbstractInstanceManager, args: Namespace, output: AbstractOutputWriter):

        instance_manager.stop(output)

        output.write('\n'
                     '----------------------------------\n'
                     'Instance was successfully deleted.\n'
                     '----------------------------------')
