import logging
from collections import OrderedDict
from time import sleep
from httplib2 import ServerNotFoundError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.resources.instance import Instance
from spotty.providers.gcp.resources.stack import Stack
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.helpers.dm_client import DMClient
from spotty.providers.gcp.helpers.dm_resource import DMResource


def wait_resources(dm: DMClient, ce: CEClient, deployment_name: str, resource_messages: OrderedDict,
                   instance_resource_name: str, machine_name: str, output: AbstractOutputWriter, delay: int = 5):
    # make sure that the instance resource is in the messages list
    assert any(resource_name == instance_resource_name for resource_name, _ in resource_messages.items())

    created_resources = set()
    for resource_name, message in resource_messages.items():
        output.write('- %s...' % message)

        is_created = False
        while not is_created:
            sleep(delay)

            # get the resource info
            try:
                # check that the deployment is not failed
                stack = Stack.get_by_name(dm, deployment_name)
                if stack.error:
                    raise ValueError('Deployment "%s" failed.\n'
                                     'Error: %s' % (deployment_name, stack.error['message']))

                # check if the instance was preempted, terminated or deleted right after creation
                if instance_resource_name in created_resources:
                    instance = Instance.get_by_name(ce, machine_name)
                    if not instance or instance.is_stopped:
                        raise ValueError('Error: the instance was unexpectedly terminated. Please, check out the '
                                         'instance logs to find out the reason.\n')

                # get resource
                resource = DMResource.get_by_name(dm, deployment_name, resource_name)
            except (ConnectionResetError, ServerNotFoundError):
                logging.warning('Connection problem')
                continue

            # resource doesn't exist yet
            if not resource:
                continue

            # resource failed
            if resource.is_failed:
                error_msg = ('Error: ' + resource.error_message) if resource.error_message \
                    else 'Please, see Deployment Manager logs for the details.' % deployment_name

                raise ValueError('Deployment "%s" failed.\n%s' % (deployment_name, error_msg))

            # resource was successfully created
            is_created = resource.is_created

        created_resources.add(resource_name)


def check_gpu_configuration(ce: CEClient, gpu_parameters: dict):
    if not gpu_parameters:
        return

    # check GPU type
    accelerator_types = ce.get_accelerator_types()
    gpu_type = gpu_parameters['type']
    if gpu_type not in accelerator_types:
        if accelerator_types:
            error_msg = 'GPU type "%s" is not supported in the "%s" zone.\nAvailable GPU types are: %s.' \
                        % (gpu_type, ce.zone, ', '.join(accelerator_types.keys()))
        else:
            error_msg = 'The "%s" zone doesn\'t support any GPU accelerators.' % ce.zone

        raise ValueError(error_msg)

    # check the number of GPUs is not exceed the maximum
    max_cards_per_instance = accelerator_types[gpu_parameters['type']]
    if gpu_parameters['count'] > max_cards_per_instance:
        raise ValueError('Maximum allowed number of cards per instance for the "%s" type is %d.'
                         % (gpu_parameters['type'], max_cards_per_instance))

