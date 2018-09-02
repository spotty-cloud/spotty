import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import wait_stack_status_changed
from spotty.helpers.validation import validate_instance_config
from spotty.project_resources.stack import StackResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class StopCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'stop'

    @staticmethod
    def get_description():
        return 'Terminate running instance and delete its stack'

    @staticmethod
    def _validate_config(config):
        return validate_instance_config(config)

    def run(self, output: AbstractOutputWriter):
        project_config = self._config['project']
        instance_config = self._config['instance']

        project_name = project_config['name']
        region = instance_config['region']

        cf = boto3.client('cloudformation', region_name=region)

        stack = StackResource(cf, project_name, region)

        # check that the stack exists
        if not stack.stack_exists():
            raise ValueError('Stack "%s" doesn\'t exists.' % stack.name)

        # get stack ID
        stack_info = stack.get_stack_info()
        stack_id = stack_info['StackId']

        # delete the stack
        stack.delete_stack()

        output.write('Waiting for the stack to be deleted...')

        resource_messages = [
            ('TerminateInstance', 'terminating the instance'),
            ('_', 'creating snapshots and deleting the volumes'),
        ]

        # wait for the deletion to be completed
        status, stack_info = wait_stack_status_changed(cf, stack_id=stack_id, waiting_status='DELETE_IN_PROGRESS',
                                                       resource_messages=resource_messages,
                                                       resource_success_status='DELETE_COMPLETE', output=output)

        if status == 'DELETE_COMPLETE':
            output.write('\n'
                         '--------------------\n'
                         'Stack was successfully deleted.\n'
                         '--------------------')
        else:
            raise ValueError('Stack "%s" was not deleted.\n'
                             'See CloudFormation and CloudWatch logs for details.' % stack.name)
