from collections import namedtuple
from time import sleep
from typing import List, Dict
from botocore.exceptions import EndpointConnectionError, ClientError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


Task = namedtuple('Task', ['message', 'start_resource', 'finish_resource', 'enabled'])


class Stack(object):

    def __init__(self, cf, stack_info):
        self._cf = cf
        self._stack_info = stack_info

    @staticmethod
    def get_by_name(cf, stack_name: str):
        """Returns a Stack by its name."""
        try:
            res = cf.describe_stacks(StackName=stack_name)
        except ClientError as e:
            # ignore an exception if it raised because the stack doesn't exist
            error_code = e.response.get('Error', {}).get('Code')
            if error_code != 'ValidationError':
                raise e

            res = {'Stacks': []}

        if not len(res['Stacks']):
            return None

        return Stack(cf, res['Stacks'][0])

    @staticmethod
    def create_stack(cf, *args, **kwargs):
        res = cf.create_stack(*args, **kwargs)
        return Stack(cf, res)

    @staticmethod
    def update_stack(cf, *args, **kwargs):
        res = cf.update_stack(*args, **kwargs)
        return Stack(cf, res)

    @property
    def stack_id(self) -> str:
        return self._stack_info['StackId']

    @property
    def stack_uuid(self) -> str:
        return self.stack_id.rsplit('/', 1)[-1]

    @property
    def name(self) -> str:
        return self._stack_info['StackName']

    @property
    def status(self) -> str:
        return self._stack_info['StackStatus']

    @property
    def outputs(self) -> str:
        return self._stack_info['Outputs']

    def delete(self):
        return self._cf.delete_stack(StackName=self.stack_id)

    def wait_stack_created(self, delay=30):
        waiter = self._cf.get_waiter('stack_create_complete')
        waiter.wait(StackName=self.stack_id, WaiterConfig={'Delay': delay})

    def wait_stack_updated(self, delay=30):
        waiter = self._cf.get_waiter('stack_update_complete')
        waiter.wait(StackName=self.stack_id, WaiterConfig={'Delay': delay})

    def wait_stack_deleted(self, delay=30):
        waiter = self._cf.get_waiter('stack_delete_complete')
        waiter.wait(StackName=self.stack_id, WaiterConfig={'Delay': delay})

    def wait_status_changed(self, stack_waiting_status: str, output: AbstractOutputWriter, delay: int = 5):
        stack = None
        while True:
            # get the latest status of the stack
            try:
                stack = self.get_by_name(self._cf, self.stack_id)
            except EndpointConnectionError as e:
                output.write(str(e))
                continue

            if stack.status != stack_waiting_status:
                break

            sleep(delay)

        return stack

    def wait_tasks(self, tasks: List[Task], resource_success_status: str, resource_fail_status: str,
                   output: AbstractOutputWriter, delay: int = 5):
        resource_statuses = self._get_resource_statuses()

        for task in tasks:
            if not task.enabled:
                continue

            task_started = task_finished = False
            while not task_finished:
                start_status = resource_statuses.get(task.start_resource)
                finish_status = resource_statuses.get(task.finish_resource)

                if not task_started and (not task.start_resource or (start_status == resource_success_status)):
                    task_started = True
                    output.write('- %s... ' % task.message, newline=False)
                elif task_started and (finish_status == resource_success_status):
                    task_finished = True
                    output.write('DONE')
                else:
                    sleep(delay)
                    try:
                        resource_statuses = self._get_resource_statuses()
                    except EndpointConnectionError as e:
                        output.write(str(e))
                        continue

                    # check that the stack is not failed
                    for status in resource_statuses.values():
                        if status == resource_fail_status:
                            if task_started and not task_finished:
                                output.write('')
                            return

    def _get_resource_statuses(self) -> Dict[str, str]:
        stack_resources = self._cf.list_stack_resources(StackName=self.stack_id)

        resource_statuses = {row['LogicalResourceId']: row['ResourceStatus']
                             for row in stack_resources['StackResourceSummaries']}

        return resource_statuses
