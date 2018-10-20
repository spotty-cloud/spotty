from time import sleep
from botocore.exceptions import EndpointConnectionError, WaiterError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


def get_snapshot(ec2, snapshot_name: str):
    """Returns a snapshot by its name."""
    res = ec2.describe_snapshots(Filters=[
        {'Name': 'tag:Name', 'Values': [snapshot_name]},
    ])

    if len(res['Snapshots']) > 1:
        raise ValueError('Several snapshots with Name=%s found.' % snapshot_name)

    snapshot = res['Snapshots'][0] if len(res['Snapshots']) else {}

    return snapshot


def get_volume(ec2, volume_name: str):
    """Returns the volume by its name."""
    res = ec2.describe_volumes(Filters=[
        {'Name': 'tag:Name', 'Values': [volume_name]},
        {'Name': 'status', 'Values': ['available']},
    ])

    if len(res['Volumes']) > 1:
        raise ValueError('Several volumes with Name=%s found.' % volume_name)

    volume = res['Volumes'][0] if len(res['Volumes']) else {}

    return volume


def get_instance_ip_address(ec2, stack_name):
    instances_info = ec2.describe_instances(Filters=[
        {'Name': 'tag:aws:cloudformation:stack-name', 'Values': [stack_name]},
        {'Name': 'instance-state-name', 'Values': ['running']},
    ])

    if not len(instances_info['Reservations']):
        raise ValueError('Instance is not running.\n'
                         'Use "spotty start" command to run an instance.')

    ip_address = instances_info['Reservations'][0]['Instances'][0]['PublicIpAddress']

    return ip_address


def stack_exists(cf, stack_name):
    res = True
    try:
        cf.get_waiter('stack_exists').wait(StackName=stack_name, WaiterConfig={'MaxAttempts': 1})
    except WaiterError:
        res = False

    return res


def wait_stack_status_changed(cf, stack_id, waiting_status, resource_messages, resource_success_status,
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
                stack_resources = cf.list_stack_resources(StackName=stack_id)
            except EndpointConnectionError:
                output.write('Connection problem')
                continue

            resource_statuses = dict([(row['LogicalResourceId'], row['ResourceStatus'])
                                      for row in stack_resources['StackResourceSummaries']])

            while (resource_name is None) or (resource_name and
                                              resource_statuses.get(resource_name, '') == resource_success_status):
                (resource_name, resource_msg) = next(resource_messages, (False, False))
                if resource_name:
                    output.write('  - %s...' % resource_msg)

        # get the latest status of the stack
        try:
            res = cf.describe_stacks(StackName=stack_id)
        except EndpointConnectionError:
            output.write('Connection problem')
            continue

        stack = res['Stacks'][0]
        current_status = stack['StackStatus']

    return current_status, stack


def is_gpu_instance(instance_type: str):
    return instance_type in [
        'p2.xlarge', 'p2.8xlarge', 'p2.16xlarge',
        'p3.2xlarge', 'p3.8xlarge', 'p3.16xlarge',
        'g3s.xlarge', 'g3.4xlarge', 'g3.8xlarge', 'g3.16xlarge',
    ]


def is_valid_instance_type(instance_type: str):
    return instance_type in [
        't1.micro',
        't2.nano', 't2.micro', 't2.small', 't2.medium', 't2.large', 't2.xlarge', 't2.2xlarge',
        'm1.small', 'm1.medium', 'm1.large', 'm1.xlarge',
        'm3.medium', 'm3.large', 'm3.xlarge', 'm3.2xlarge',
        'm4.large', 'm4.xlarge', 'm4.2xlarge', 'm4.4xlarge', 'm4.10xlarge', 'm4.16xlarge',
        'm2.xlarge', 'm2.2xlarge', 'm2.4xlarge',
        'cr1.8xlarge',
        'r3.large', 'r3.xlarge', 'r3.2xlarge', 'r3.4xlarge', 'r3.8xlarge',
        'r4.large', 'r4.xlarge', 'r4.2xlarge', 'r4.4xlarge', 'r4.8xlarge', 'r4.16xlarge',
        'x1.16xlarge', 'x1.32xlarge',
        'x1e.xlarge', 'x1e.2xlarge', 'x1e.4xlarge', 'x1e.8xlarge', 'x1e.16xlarge', 'x1e.32xlarge',
        'i2.xlarge', 'i2.2xlarge', 'i2.4xlarge', 'i2.8xlarge',
        'i3.large', 'i3.xlarge', 'i3.2xlarge', 'i3.4xlarge', 'i3.8xlarge', 'i3.16xlarge', 'i3.metal',
        'hi1.4xlarge',
        'hs1.8xlarge',
        'c1.medium', 'c1.xlarge',
        'c3.large', 'c3.xlarge', 'c3.2xlarge', 'c3.4xlarge', 'c3.8xlarge',
        'c4.large', 'c4.xlarge', 'c4.2xlarge', 'c4.4xlarge', 'c4.8xlarge',
        'c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge', 'c5.18xlarge',
        'c5d.large', 'c5d.xlarge', 'c5d.2xlarge', 'c5d.4xlarge', 'c5d.9xlarge', 'c5d.18xlarge',
        'cc1.4xlarge',
        'cc2.8xlarge',
        'g2.2xlarge', 'g2.8xlarge',
        'g3s.xlarge', 'g3.4xlarge', 'g3.8xlarge', 'g3.16xlarge',
        'cg1.4xlarge',
        'p2.xlarge', 'p2.8xlarge', 'p2.16xlarge',
        'p3.2xlarge', 'p3.8xlarge', 'p3.16xlarge',
        'd2.xlarge', 'd2.2xlarge', 'd2.4xlarge', 'd2.8xlarge',
        'f1.2xlarge', 'f1.16xlarge',
        'm5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge', 'm5.12xlarge', 'm5.24xlarge',
        'm5d.large', 'm5d.xlarge', 'm5d.2xlarge', 'm5d.4xlarge', 'm5d.12xlarge', 'm5d.24xlarge',
        'h1.2xlarge', 'h1.4xlarge', 'h1.8xlarge', 'h1.16xlarge',
    ]
