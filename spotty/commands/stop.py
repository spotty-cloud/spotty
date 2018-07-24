import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.utils.stack import wait_for_status_changed, stack_exists
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class StopCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'stop'

    def run(self, output: AbstractOutputWriter):
        # TODO: check config
        region = self._config['instance']['region']
        stack_name = self._config['instance']['stackName']

        cf = boto3.client('cloudformation', region_name=region)

        # check that the stack exists
        if not stack_exists(cf, stack_name):
            raise ValueError('Stack "%s" doesn\'t exists.' % stack_name)

        # get image info
        res = cf.describe_stacks(StackName=stack_name)
        stack_id = res['Stacks'][0]['StackId']

        # delete the image
        cf.delete_stack(StackName=stack_id)

        output.write('Waiting for the stack to be deleted...')

        # wait for the deletion to be completed
        status, stack = wait_for_status_changed(cf, stack_id=stack_id, waiting_status='DELETE_IN_PROGRESS',
                                                output=output)

        if status == 'DELETE_COMPLETE':
            output.write('Stack was successfully deleted.')
        else:
            raise ValueError('Stack "%s" not deleted. See CloudFormation and CloudWatch logs for details.' % stack_id)
