from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class StartCommand(AbstractConfigCommand):

    name = 'start'
    description = 'Run spot instance, sync the project and start the Docker container'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('--dry-run', action='store_true', help='Displays the steps that would be performed '
                                                                   'using the specified command without actually '
                                                                   'running them')

    def _run(self, project_dir: str, config: dict, args: Namespace, output: AbstractOutputWriter):
        project_name = config['project']['name']
        sync_filters = config['project']['syncFilters']
        container_config = config['container']
        instance_config = get_instance_config(config['instances'], args.instance_name)

        instance = InstanceFactory.get_instance(project_name, instance_config)

        # check if the stack with the instance is already created
        if instance.is_created():
            raise ValueError('Instance "%s" is already started.\n'
                             'Use "spotty stop" command to stop the instance.' % args.instance_name)

        # start the instance
        dry_run = args.dry_run
        with output.prefix('[dry-run] ' if dry_run else ''):
            instance.start(project_dir, sync_filters, container_config, output, dry_run)

        if not dry_run:
            output.write('\n' + instance.status_text)
            output.write('\nUse "spotty ssh" command to connect to the Docker container.\n')
