import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.aws_resources.stack import Stack
from spotty.utils import random_string


class AmiStackResource(object):

    def __init__(self, region):
        self._cf = boto3.client('cloudformation', region_name=region)

    def create_stack(self, template: str, instance_type: str, ami_name: str, key_name: str,
                     keep_instance: bool, output: AbstractOutputWriter):
        """Runs CloudFormation template."""
        params = {
            'InstanceType': instance_type,
            'ImageName': ami_name,
        }

        if key_name:
            params['KeyName'] = key_name

        stack_name = 'spotty-nvidia-docker-ami-%s' % random_string(8)
        stack = Stack.create_stack(
            cf=self._cf,
            StackName=stack_name,
            TemplateBody=template,
            Parameters=[{'ParameterKey': key, 'ParameterValue': value} for key, value in params.items()],
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DO_NOTHING' if keep_instance else 'DELETE',
        )

        output.write('Waiting for the AMI to be created...')

        resource_messages = [
            ('InstanceProfile', 'creating IAM role for the instance'),
            ('SpotInstance', 'launching the instance'),
            ('InstanceReadyWaitCondition', 'installing NVIDIA Docker'),
            ('AMICreatedWaitCondition', 'creating AMI and terminating the instance'),
        ]

        # wait for the stack to be created
        with output.prefix('  '):
            stack = stack.wait_status_changed(waiting_status='CREATE_IN_PROGRESS',
                                              resource_messages=resource_messages,
                                              resource_success_status='CREATE_COMPLETE', output=output)

        if stack.status == 'CREATE_COMPLETE':
            ami_id = [row['OutputValue'] for row in stack.outputs if row['OutputKey'] == 'NewAMI'][0]

            output.write('\n'
                         '--------------------------------------------------\n'
                         'AMI "%s" (ID=%s) was successfully created.\n'
                         'Use "spotty start" command to run a Spot Instance.\n'
                         '--------------------------------------------------'
                         % (ami_name, ami_id))
        else:
            raise ValueError('Stack "%s" was not created.\n'
                             'See CloudFormation and CloudWatch logs for details.' % stack_name)
