from collections import OrderedDict
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.gcp_resources.stack import Stack
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.helpers.deployment import wait_resources
from spotty.providers.gcp.helpers.dm_client import DMClient


class ImageStackResource(object):

    def __init__(self, image_name: str, project_id: str, zone: str):
        self._dm = DMClient(project_id, zone)
        self._ce = CEClient(project_id, zone)
        self._image_name = image_name
        self._stack_name = 'spotty-image-%s' % image_name

    def get_stack(self):
        return Stack.get_by_name(self._dm, self._stack_name)

    def create_stack(self, template: str, machine_name: str, debug_mode: bool, output: AbstractOutputWriter):
        """Creates an image stack and waits for the image to be created."""

        # check that the stack doesn't exist
        if self.get_stack():
            raise ValueError('Deployment "%s" already exists.' % self._stack_name)

        # create stack
        Stack.create(self._dm, self._stack_name, template)

        output.write('Waiting for the image to be created...')

        resource_messages = OrderedDict([
            (machine_name, 'launching the instance'),
            ('%s-docker-waiter' % machine_name, 'installing NVIDIA Docker'),
        ])

        if not debug_mode:
            resource_messages['%s-image-waiter' % machine_name] = 'creating an image and terminating the instance'

        # wait for the stack to be created
        with output.prefix('  '):
            wait_resources(self._dm, self._ce, self._stack_name, resource_messages,
                           instance_resource_name=machine_name, machine_name=machine_name, output=output)

        if debug_mode:
            output.write('Stack "%s" was created in debug mode.' % self._stack_name)
        else:
            output.write('\n'
                         '--------------------------------------------------\n'
                         'Image "%s" was successfully created.\n'
                         'Use the "spotty start" command to run an instance.\n'
                         '--------------------------------------------------'
                         % self._image_name)

    def delete_stack(self, output: AbstractOutputWriter):
        # check that the stack exist
        stack = self.get_stack()
        if not stack:
            raise ValueError('Deployment "%s" not found.' % self._stack_name)

        output.write('Waiting for the deployment to be deleted...')

        # delete the stack
        try:
            stack.delete()
            stack.wait_stack_deleted()
        except Exception as e:
            raise ValueError('Deployment "%s" was not deleted. Error: %s\n'
                             'See Deployment Manager logs for details.' % (self._stack_name, str(e)))

        output.write('\n'
                     '-------------------------------\n'
                     'Image was successfully deleted.\n'
                     '-------------------------------')
