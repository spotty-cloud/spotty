from argparse import Namespace
from spotty.commands.abstract_config_command import AbstractConfigCommand
from spotty.helpers.config import get_instance_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.instance_factory import InstanceFactory


class StartCommand(AbstractConfigCommand):

    name = 'start'
    description = 'Run spot instance, sync the project and start the Docker container'

    def _run(slf, project_dir: str, config: dict, args: Namespace, output: AbstractOutputWriter):
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
        instance.start(project_dir, sync_filters, container_config, output)

        output.write('\n' + instance.status_text)
        output.write('\nUse "spotty ssh" command to connect to the Docker container.\n')
