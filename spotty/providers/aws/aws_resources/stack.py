from time import sleep
from botocore.exceptions import EndpointConnectionError, ClientError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


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

    def wait_status_changed(self, waiting_status, resource_messages, resource_success_status,
                            output: AbstractOutputWriter, delay=5):
        current_status = waiting_status
        stack = None

        resource_messages = iter(resource_messages) if resource_messages else None
        resource_name = None

        while current_status == waiting_status:
            sleep(delay)

            # display resource creation progress
            if resource_messages:
                try:
                    stack_resources = self._cf.list_stack_resources(StackName=self.stack_id)
                except EndpointConnectionError:
                    output.write('Connection problem')
                    continue

                resource_statuses = dict([(row['LogicalResourceId'], row['ResourceStatus'])
                                          for row in stack_resources['StackResourceSummaries']])

                while (resource_name is None) or (resource_name and
                                                  resource_statuses.get(resource_name, '') == resource_success_status):
                    (resource_name, resource_msg) = next(resource_messages, (False, False))
                    if resource_name:
                        output.write('- %s...' % resource_msg)

            # get the latest status of the stack
            try:
                stack = self.get_by_name(self._cf, self.stack_id)
            except EndpointConnectionError:
                output.write('Connection problem')
                continue

            current_status = stack.status

        return stack
