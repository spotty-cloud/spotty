import logging
from collections import OrderedDict
from time import sleep
from httplib2 import ServerNotFoundError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.helpers.ce_client import CEClient
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


def check_gpu_configuration(ce: CEClient, gpu_parameters: dict):
    if not gpu_parameters:
        return

    # check GPU type
    accelerator_types = ce.get_accelerator_types()
    gpu_type = gpu_parameters['type']
    if gpu_type not in accelerator_types:
        raise ValueError('GPU type "%s" is not supported in the "%s" zone.\nAvailable GPU types are: %s.' %
                         (gpu_type, ce.zone, ', '.join(accelerator_types.keys())))

    # check the number of GPUs is not exceed the maximum
    max_cards_per_instance = accelerator_types[gpu_parameters['type']]
    if gpu_parameters['count'] > max_cards_per_instance:
        raise ValueError('Maximum allowed number of cards per instance for the "%s" type is %d.'
                         % (gpu_parameters['type'], max_cards_per_instance))

