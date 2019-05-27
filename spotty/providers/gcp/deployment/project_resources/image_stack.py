from collections import OrderedDict
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.helpers.deployment import wait_resources
from spotty.providers.gcp.helpers.dm_client import DMClient


class ImageStack(object):

    def __init__(self, image_name: str, project_id: str, zone: str):
        self._dm = DMClient(project_id, zone)
        self._image_name = image_name
        self._stack_name = 'spotty-image-%s' % image_name

    def create_stack(self, template: str, machine_name: str, debug_mode: bool, output: AbstractOutputWriter):
        """Creates an image stack and waits for the image to be created."""

        # check that the stack doesn't exist
        res = self._dm.get(self._stack_name)
        if res:
            raise ValueError('Deployment "%s" already exists.' % self._stack_name)

        # create stack
        self._dm.deploy(self._stack_name, template)

        output.write('Waiting for the image to be created...')

        resource_messages = OrderedDict([
            (machine_name, 'launching the instance'),
            ('%s-docker-waiter' % machine_name, 'installing NVIDIA Docker'),
            ('%s-image-waiter' % machine_name, 'creating an image and terminating the instance'),
        ])

        # wait for the stack to be created
        with output.prefix('  '):
            wait_resources(self._dm, self._stack_name, resource_messages, output)

        if debug_mode:
            output.write('Stack "%s" was created in debug mode.' % self._stack_name)
        else:
            output.write('\n'
                         '--------------------------------------------------\n'
                         'Image "%s" was successfully created.\n'
                         'Use the "spotty start" command to run an instance.\n'
                         '--------------------------------------------------'
                         % self._image_name)
