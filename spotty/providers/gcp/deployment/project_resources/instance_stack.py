from collections import OrderedDict
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.gcp_resources.stack import Stack
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.helpers.deployment import wait_resources
from spotty.providers.gcp.helpers.dm_client import DMClient


class InstanceStackResource(object):

    def __init__(self, machine_name: str, project_id: str, zone: str):
        self._dm = DMClient(project_id, zone)
        self._ce = CEClient(project_id, zone)
        self._machine_name = machine_name
        self._stack_name = 'spotty-instance-' + machine_name

    @property
    def name(self):
        return self._stack_name

    def create_or_update_stack(self, template: str, output: AbstractOutputWriter):
        """Deploys a Deployment Manager template."""

        # delete the stack if it exists
        self.delete_stack(output)

        # create stack
        self._dm.deploy(self._stack_name, template)

        output.write('Waiting for the stack to be created...')

        resource_messages = OrderedDict([
            (self._machine_name, 'launching the instance'),
            (self._machine_name + '-docker-waiter', 'running the Docker container'),
        ])

        # wait for the stack to be created
        with output.prefix('  '):
            wait_resources(self._dm, self._stack_name, resource_messages, output)

    def delete_stack(self, output: AbstractOutputWriter, no_wait=False):
        stack = Stack.get_by_name(self._dm, self._stack_name)
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
                             'See Deployment Manager logs for details.' % (self._stack_name, str(e)))
