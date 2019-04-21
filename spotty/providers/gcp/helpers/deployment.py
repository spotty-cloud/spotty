from time import sleep
from httplib2 import ServerNotFoundError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.helpers.dm_client import DMClient


def wait_resources(dm: DMClient, deployment_name: str, resource_messages: dict, output: AbstractOutputWriter, delay=5):
    cur_states = dm.get_resources_states(deployment_name)
    prev_states = {}

    while True:
        if cur_states:
            is_completed = True
            for resource_name, state in cur_states.items():
                # print a message once a resource gets the "IN_PROGRESS" status
                if (not prev_states or (prev_states[resource_name] != state)) \
                        and (state in ['IN_PROGRESS', 'IN_PREVIEW']) \
                        and (resource_name in resource_messages):
                    output.write('- %s...' % resource_messages[resource_name])

                # check that the resources are not failed
                if state not in [None, 'PENDING', 'IN_PROGRESS', 'COMPLETED', 'IN_PREVIEW']:
                    raise ValueError('Deployment "%s" failed.\n'
                                     'Please, see Deployment Manager logs for the details.' % deployment_name)

                if state not in ['COMPLETED', 'IN_PREVIEW']:
                    is_completed = False

            # check if the deployment is completed
            if is_completed:
                break

            prev_states = cur_states

        sleep(delay)

        try:
            cur_states = dm.get_resources_states(deployment_name)
        except (ConnectionResetError, ServerNotFoundError):
            output.write('Connection problem')
            continue
