from collections import OrderedDict
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.resources.stack import Stack
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.helpers.deployment import wait_resources
from spotty.providers.gcp.helpers.dm_client import DMClient
from spotty.providers.gcp.helpers.dm_resource import DMResource
from spotty.providers.gcp.helpers.rtc_client import RtcClient


class InstanceStackManager(object):

    def __init__(self, machine_name: str, project_id: str, zone: str):
        self._dm = DMClient(project_id, zone)
        self._ce = CEClient(project_id, zone)
        self._rtc = RtcClient(project_id, zone)
        self._machine_name = machine_name
        self._stack_name = 'spotty-instance-' + machine_name

        # resource names
        self._INSTANCE_RESOURCE_NAME = machine_name
        self._DOCKER_WAITER_RESOURCE_NAME = machine_name + '-docker-waiter'
        self._DOCKER_STATUS_CONFIG_RESOURCE_NAME = machine_name + '-docker-status'

    @property
    def name(self):
        return self._stack_name

    def create_stack(self, template: str, output: AbstractOutputWriter):
        """Deploys a Deployment Manager template."""

        # create a stack
        res = Stack.create(self._dm, self._stack_name, template)
        # print(res)
        # exit()

        output.write('Waiting for the stack to be created...')

        resource_messages = OrderedDict([
            (self._INSTANCE_RESOURCE_NAME, 'launching the instance'),
            (self._DOCKER_WAITER_RESOURCE_NAME, 'running the Docker container'),
        ])

        # wait for the stack to be created
        with output.prefix('  '):
            wait_resources(self._dm, self._ce, self._stack_name, resource_messages,
                           instance_resource_name=self._INSTANCE_RESOURCE_NAME, machine_name=self._machine_name,
                           output=output)

    def delete_stack(self, output: AbstractOutputWriter):
        stack = Stack.get_by_name(self._dm, self._stack_name)
        if not stack:
            return

        output.write('Waiting for the stack to be deleted...')

        # delete the stack
        try:
            if stack.is_running:
                # stop an ongoing operation first to make sure the delete method
                # won't raise an error "Resource '...' has an ongoing conflicting operation"
                stack.stop()

                # if the docker-waiter resource is still waiting for a signal, send a failure signal
                # to be able to delete the stack
                resource = DMResource.get_by_name(self._dm, self._stack_name, self._DOCKER_WAITER_RESOURCE_NAME)
                if resource.is_in_progress:
                    self._rtc.set_value(self._DOCKER_STATUS_CONFIG_RESOURCE_NAME, '/failure/1', '1')

                # wait until the stack will be created or will fail
                stack.wait_stack_done()

            stack.delete()
            stack.wait_stack_deleted()
        except Exception as e:
            raise ValueError('Stack "%s" was not deleted. Error: %s\n'
                             'See Deployment Manager logs for details.' % (self._stack_name, str(e)))
