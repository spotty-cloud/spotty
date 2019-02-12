import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.aws_resources.stack import Stack
from spotty.utils import random_string


class AmiStackResource(object):

    def __init__(self, region):
        self._cf = boto3.client('cloudformation', region_name=region)

    def create_stack(self, template: str, parameters: dict, debug_instance: bool, output: AbstractOutputWriter):
        """Runs CloudFormation template."""
        stack_name = 'spotty-nvidia-docker-ami-%s' % random_string(8)
        stack = Stack.create_stack(
            cf=self._cf,
            StackName=stack_name,
            TemplateBody=template,
            Parameters=[{'ParameterKey': key, 'ParameterValue': value} for key, value in parameters.items()],
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DO_NOTHING' if debug_instance else 'DELETE',
        )

        output.write('Waiting for the AMI to be created...')

        resource_messages = [
            ('InstanceProfile', 'creating IAM role for the instance'),
            ('Instance', 'launching the instance'),
            ('InstanceReadyWaitCondition', 'installing NVIDIA Docker'),
            ('AMICreatedWaitCondition', 'creating AMI and terminating the instance'),
        ]

        # wait for the stack to be created
        with output.prefix('  '):
            stack = stack.wait_status_changed(waiting_status='CREATE_IN_PROGRESS',
                                              resource_messages=resource_messages,
                                              resource_success_status='CREATE_COMPLETE', output=output)

        if stack.status != 'CREATE_COMPLETE':
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation logs for the details.' % stack_name)

        ami_id = [row['OutputValue'] for row in stack.outputs if row['OutputKey'] == 'NewAMI'][0]

        output.write('\n'
                     '--------------------------------------------------\n'
                     'AMI "%s" (ID=%s) was successfully created.\n'
                     'Use the "spotty start" command to run an instance.\n'
                     '--------------------------------------------------'
                     % (parameters['ImageName'], ami_id))

    def delete_stack(self, stack_id, output: AbstractOutputWriter):
        # delete the image
        stack = Stack.get_by_name(self._cf, stack_id)
        stack.delete()

        output.write('Waiting for the AMI to be deleted...')

        # wait for the deletion to be completed
        with output.prefix('  '):
            stack = stack.wait_status_changed(waiting_status='DELETE_IN_PROGRESS',
                                              resource_messages=[],
                                              resource_success_status='DELETE_COMPLETE', output=output)

        if stack.status == 'DELETE_COMPLETE':
            output.write('\n'
                         '-----------------------------\n'
                         'AMI was successfully deleted.\n'
                         '-----------------------------')
        else:
            raise ValueError('Stack "%s" not deleted.\n'
                             'See CloudFormation and CloudWatch logs for details.' % stack_id)
