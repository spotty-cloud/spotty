import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.aws_resources.instance import Instance
from spotty.providers.aws.aws_resources.stack import Stack


class InstanceStackResource(object):

    def __init__(self, project_name: str, instance_name: str, region: str):
        self._cf = boto3.client('cloudformation', region_name=region)
        self._ec2 = boto3.client('ec2', region_name=region)
        self._region = region
        self._stack_name = 'spotty-instance-%s-%s' % (project_name.lower(), instance_name.lower())

    @property
    def name(self):
        return self._stack_name

    def get_instance(self):
        return Instance.get_by_stack_name(self._ec2, self.name)

    def create_or_update_stack(self, template: str, parameters: dict, output: AbstractOutputWriter):
        """Runs CloudFormation template."""

        # delete the stack if it exists
        stack = Stack.get_by_name(self._cf, self._stack_name)
        if stack:
            self.delete_stack(output)

        # create new stack
        stack = Stack.create_stack(
            cf=self._cf,
            StackName=self._stack_name,
            TemplateBody=template,
            Parameters=[{'ParameterKey': key, 'ParameterValue': value} for key, value in parameters.items()],
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DO_NOTHING',
        )

        output.write('Waiting for the stack to be created...')

        resource_messages = [
            ('Instance', 'launching the instance'),
            ('DockerReadyWaitCondition', 'waiting for the Docker container to be ready'),
        ]

        # wait for the stack to be created
        with output.prefix('  '):
            stack = stack.wait_status_changed(waiting_status='CREATE_IN_PROGRESS',
                                              resource_messages=resource_messages,
                                              resource_success_status='CREATE_COMPLETE', output=output)

        if stack.status != 'CREATE_COMPLETE':
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation logs for the details.'
                             % self._stack_name)

        return stack

    def delete_stack(self, output: AbstractOutputWriter, no_wait=False):
        stack = Stack.get_by_name(self._cf, self._stack_name)
        if not stack:
            return

        if not no_wait:
            output.write('Waiting for the stack to be deleted...')

        # delete the stack
        try:
            stack.delete()
            if not no_wait:
                stack.wait_stack_deleted()
        except Exception as e:
            raise ValueError('Stack "%s" was not deleted. Error: %s\n'
                             'See CloudFormation logs for details.' % (self._stack_name, str(e)))
