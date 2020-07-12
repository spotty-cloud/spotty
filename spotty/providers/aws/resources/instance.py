from datetime import datetime
from spotty.deployment.abstract_cloud_instance.resources.abstract_instance import AbstractInstance
from spotty.providers.aws.helpers.instance_prices import get_current_spot_price, get_on_demand_price


class Instance(AbstractInstance):

    def __init__(self, ec2, data: dict):
        self._ec2 = ec2
        self._data = data

    @staticmethod
    def get_by_stack_name(ec2, stack_name):
        """Returns the running instance by its stack name
           or None if the instance is not running.
        """
        res = ec2.describe_instances(Filters=[
            {'Name': 'tag:aws:cloudformation:stack-name', 'Values': [stack_name]},
            {'Name': 'instance-state-name', 'Values': ['running']},
        ])

        if len(res['Reservations']) > 1:
            raise ValueError('Several running instances for the stack "%s" are found.' % stack_name)

        if not len(res['Reservations']):
            return None

        return Instance(ec2, res['Reservations'][0]['Instances'][0])

    @property
    def instance_id(self):
        return self._data['InstanceId']

    @property
    def public_ip_address(self) -> str:
        return self._data.get('PublicIpAddress', None)

    @property
    def state(self) -> str:
        return self._data['State']['Name']

    @property
    def instance_type(self) -> str:
        return self._data['InstanceType']

    @property
    def availability_zone(self) -> str:
        return self._data['Placement']['AvailabilityZone']

    @property
    def launch_time(self) -> datetime:
        return self._data['LaunchTime']

    @property
    def lifecycle(self) -> str:
        return self._data.get('InstanceLifecycle')

    @property
    def is_running(self):
        return self.state == 'running'

    @property
    def is_stopped(self):
        return self.state == 'stopped'

    def get_spot_price(self):
        """Get current Spot Instance price for this instance."""
        return get_current_spot_price(self._ec2, self.instance_type, self.availability_zone)

    def get_on_demand_price(self):
        """Get On-demand Instance price for the same instance in the us-east-1 region."""
        return get_on_demand_price(self.instance_type, 'us-east-1')

    def terminate(self, wait: bool = True):
        self._ec2.terminate_instances(InstanceIds=[self.instance_id])
        if wait:
            waiter = self._ec2.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=[self.instance_id])

    def stop(self, wait: bool = True):
        self._ec2.stop_instances(InstanceIds=[self.instance_id])
        if wait:
            waiter = self._ec2.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=[self.instance_id])
