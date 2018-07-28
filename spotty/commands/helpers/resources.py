from time import sleep
from botocore.exceptions import EndpointConnectionError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


def get_ami_id(ec2, ami_name: str):
    res = ec2.describe_images(Filters=[
        {'Name': 'name', 'Values': [ami_name]},
    ])

    # check that the only one image with such name exists
    if len(res['Images']) > 1:
        raise ValueError('Several images with Name=%s found.' % ami_name)

    ami_id = res['Images'][0]['ImageId'] if len(res['Images']) else False

    return ami_id


def get_snapshot(ec2, snapshot_name: str):
    res = ec2.describe_snapshots(Filters=[
        {'Name': 'tag:Name', 'Values': [snapshot_name]},
    ])

    if len(res['Snapshots']) > 1:
        raise ValueError('Several snapshots with Name=%s found.' % snapshot_name)

    snapshot = res['Snapshots'][0] if len(res['Snapshots']) else {}

    return snapshot


def wait_for_status_changed(cf, stack_id, waiting_status, output: AbstractOutputWriter, delay=15):
    current_status = waiting_status
    stack = None
    while current_status == waiting_status:
        sleep(delay)
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
        'g3.4xlarge', 'g3.8xlarge', 'g3.16xlarge',
    ]
