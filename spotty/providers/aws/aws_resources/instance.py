from datetime import datetime
from spotty.providers.aws.helpers.spot_prices import get_current_spot_price


class Instance(object):

    def __init__(self, ec2, instance_info):
        self._ec2 = ec2
        self._instance_info = instance_info

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

    def terminate(self):
        return self._ec2.terminate_instances(InstanceIds=[self.instance_id])

    def wait_instance_terminated(self):
        waiter = self._ec2.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[self.instance_id])

    @property
    def instance_id(self):
        return self._instance_info['InstanceId']

    @property
    def public_ip_address(self) -> str:
        return self._instance_info.get('PublicIpAddress', None)

    @property
    def state(self) -> str:
        return self._instance_info['State']['Name']

    @property
    def instance_type(self) -> str:
        return self._instance_info['InstanceType']

    @property
    def availability_zone(self) -> str:
        return self._instance_info['Placement']['AvailabilityZone']

    @property
    def launch_time(self) -> datetime:
        return self._instance_info['LaunchTime']

    @property
    def lifecycle(self) -> str:
        return self._instance_info['InstanceLifecycle']

    def get_spot_price(self):
        """Get current Spot Instance price for this instance."""
        return get_current_spot_price(self._ec2, self.instance_type, self.availability_zone)
