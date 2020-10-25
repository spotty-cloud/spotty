import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.resources.stack import Stack, Task
from spotty.providers.aws.config.instance_config import InstanceConfig


class InstanceStackManager(object):

    def __init__(self, project_name: str, instance_name: str, region: str):
        self._cf = boto3.client('cloudformation', region_name=region)
        self._ec2 = boto3.client('ec2', region_name=region)
        self._region = region
        self._stack_name = 'spotty-instance-%s-%s' % (project_name.lower(), instance_name.lower())

    @property
    def name(self):
        return self._stack_name

    def create_or_update_stack(self, template: str, parameters: dict, instance_config: InstanceConfig,
                               output: AbstractOutputWriter):
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

        tasks = [
            Task(
                message='launching the instance',
                start_resource=None,
                finish_resource='Instance',
                enabled=True,
            ),
            Task(
                message='preparing the instance',
                start_resource='Instance',
                finish_resource='MountingVolumesSignal',
                enabled=True,
            ),
            Task(
                message='mounting volumes',
                start_resource='MountingVolumesSignal',
                finish_resource='SettingDockerRootSignal',
                enabled=bool(instance_config.volumes),
            ),
            Task(
                message='setting Docker data root',
                start_resource='SettingDockerRootSignal',
                finish_resource='SyncingProjectSignal',
                enabled=bool(instance_config.docker_data_root),
            ),
            Task(
                message='syncing project files',
                start_resource='SyncingProjectSignal',
                finish_resource='RunningInstanceStartupCommandsSignal',
                enabled=True,
            ),
            Task(
                message='running instance startup commands',
                start_resource='RunningInstanceStartupCommandsSignal',
                finish_resource='BuildingDockerImageSignal',
                enabled=bool(instance_config.commands),
            ),
            Task(
                message='building Docker image',
                start_resource='BuildingDockerImageSignal',
                finish_resource='StartingContainerSignal',
                enabled=bool(instance_config.dockerfile_path),
            ),
            Task(
                message='starting container',
                start_resource='StartingContainerSignal',
                finish_resource='RunningContainerStartupCommandsSignal',
                enabled=True,
            ),
            Task(
                message='running container startup commands',
                start_resource='RunningContainerStartupCommandsSignal',
                finish_resource='DockerReadyWaitCondition',
                enabled=bool(instance_config.container_config.commands),
            ),
        ]

        # wait for the stack to be created
        with output.prefix('  '):
            stack.wait_tasks(tasks, resource_success_status='CREATE_COMPLETE', resource_fail_status='CREATE_FAILED',
                             output=output)
            stack = stack.wait_status_changed(stack_waiting_status='CREATE_IN_PROGRESS', output=output)

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
