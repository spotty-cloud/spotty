import logging
from collections import OrderedDict
from time import sleep
from httplib2 import ServerNotFoundError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.helpers.dm_client import DMClient


def wait_resources(dm: DMClient, deployment_name: str, resource_messages: OrderedDict, output: AbstractOutputWriter,
                   delay: int = 5):
    for resource_name, message in resource_messages.items():
        output.write('- %s...' % message)
        while True:
            sleep(delay)

            # get the resource info
            try:
                resource = dm.get_resource(deployment_name, resource_name)
            except (ConnectionResetError, ServerNotFoundError):
                logging.warning('Connection problem')
                continue

            # resource doesn't exist yet
            if not resource:
                continue

            # resource was successfully created
            if 'finalProperties' in resource:
                break

            # an error occurred
            if 'error' in resource.get('update', {}):
                raise ValueError('Deployment "%s" failed.\n'
                                 'Error: %s'
                                 % (deployment_name, resource['update']['error']['errors'][0]['message']))

            # unexpected status
            if 'state' in resource.get('update', {}) \
                    and resource['update']['state'] not in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'IN_PREVIEW']:
                raise ValueError('Deployment "%s" failed.\n'
                                 'Please, see Deployment Manager logs for the details.' % deployment_name)
