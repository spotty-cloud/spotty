import yaml
from botocore.exceptions import WaiterError, EndpointConnectionError
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.helpers.resources import get_snapshot, get_ami_id, is_gpu_instance
from spotty.project_resources.key_pair import KeyPairResource
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.utils import data_dir


class StackResource(object):

    def __init__(self, cf, project_name: str, region: str):
        self._cf = cf
        self._project_name = project_name
        self._region = region
        self._stack_name = 'spotty-instance-%s' % project_name

    @property
    def name(self):
        return self._stack_name

    def stack_exists(self):
        res = True
        try:
            self._cf.get_waiter('stack_exists').wait(StackName=self._stack_name, WaiterConfig={'MaxAttempts': 1})
        except WaiterError:
            res = False

        return res

    def get_stack_info(self):
        try:
            res = self._cf.describe_stacks(StackName=self._stack_name)
        except EndpointConnectionError:
            res = {}

        return res['Stacks'][0]

    def prepare_template(self, ec2, volumes: list, ports: list, max_price, docker_commands,
                         output: AbstractOutputWriter):
        # read and update CF template
        with open(data_dir('run_container.yaml')) as f:
            template = yaml.load(f, Loader=CfnYamlLoader)

        # ending letters for the devices (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html)
        device_letters = 'fghijklmnop'

        # attach volumes
        block_devices = []
        create_snapshots = {}
        for i, volume in enumerate(volumes):
            block_device = {
                'DeviceName': '/dev/sd' + device_letters[i],
                'Ebs': {
                    'DeleteOnTermination': False,
                },
            }

            snapshot_name = volume['snapshotName']
            volume_size = volume['size']
            deletion_policy = volume['deletionPolicy']

            # get snapshot info
            snapshot_info = get_snapshot(ec2, snapshot_name) if snapshot_name else {}
            if not snapshot_info and not volume_size:
                raise ValueError('Size of new volume or name of existing snapshot is required.')

            if snapshot_info:
                # check size of the volume
                if volume_size:
                    if volume_size < snapshot_info['VolumeSize']:
                        raise ValueError('Requested size of the volume (%dGB) is less than size of the snapshot (%dGB).'
                                         % (volume_size, snapshot_info['VolumeSize']))
                    elif volume_size > snapshot_info['VolumeSize']:
                        output.write('Size of the snapshot will be increased from %dGB to %dGB.'
                                     % (snapshot_info['VolumeSize'], volume_size))

                # set snapshot ID
                block_device['Ebs']['SnapshotId'] = snapshot_info['SnapshotId']

                # delete the original snapshot before new snapshot will be created
                # if deletion_policy == 'snapshot':
                #     template['Resources']['DeleteSnapshot']['Properties']['SnapshotId'] = snapshot_info['SnapshotId']

            # set size of the volume
            if volume_size:
                block_device['Ebs']['VolumeSize'] = volume_size

            # set tag for new volume (future snapshot name)
            # if snapshot_name:
            #     template['Resources']['Volume1']['Properties']['Tags'] = [{'Key': 'Name', 'Value': snapshot_name}]

            if deletion_policy == 'delete':
                # delete the volume on termination
                block_device['Ebs']['DeleteOnTermination'] = True
            else:
                # create snapshots on termination
                create_snapshots[block_device['DeviceName']] = {
                    'mode': 'create' if deletion_policy == 'create_snapshot' else 'update',
                    'snapshotName': snapshot_name,
                    'snapshotId': snapshot_info['SnapshotId'] if snapshot_info else '',
                }

            block_devices.append(block_device)

        template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData'] \
            ['BlockDeviceMappings'] = block_devices
        template['Resources']['CreateSnapshots']['Properties']['Devices'] = create_snapshots

        # add ports to the security group
        for port in set(ports):
            if port != 22:
                template['Resources']['InstanceSecurityGroup']['Properties']['SecurityGroupIngress'] += [{
                    'CidrIp': '0.0.0.0/0',
                    'IpProtocol': 'tcp',
                    'FromPort': port,
                    'ToPort': port,
                }, {
                    'CidrIpv6': '::/0',
                    'IpProtocol': 'tcp',
                    'FromPort': port,
                    'ToPort': port,
                }]

        # set maximum price
        if max_price:
            template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData'] \
                ['InstanceMarketOptions']['SpotOptions']['MaxPrice'] = max_price

        # set initial docker commands
        if docker_commands:
            template['Resources']['SpotInstanceLaunchTemplate']['Metadata']['AWS::CloudFormation::Init'] \
                ['docker_container_config']['files']['/tmp/docker/docker_commands.sh']['content'] = docker_commands

        return yaml.dump(template, Dumper=CfnYamlDumper)

    def create_stack(self, ec2, template: str, instance_type: str, ami_name: str, root_volume_size: int,
                     mount_dirs: list, bucket_name: str, remote_project_dir: str, docker_config: dict):
        # get default VPC ID
        res = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        if not len(res['Vpcs']):
            raise ValueError('Default VPC not found')

        vpc_id = res['Vpcs'][0]['VpcId']

        # get image info
        ami_id = get_ami_id(ec2, ami_name)
        if not ami_id:
            raise ValueError('Image with Name=%s not found.\n'
                             'Use "spotty create-ami" command to create NVIDIA Docker AMI.' % ami_name)

        # create key pair
        project_key = KeyPairResource(ec2, self._project_name, self._region)
        key_name = project_key.create_key()

        # create stack
        params = {
            'VpcId': vpc_id,
            'InstanceType': instance_type,
            'KeyName': key_name,
            'ImageId': ami_id,
            'RootVolumeSize': str(root_volume_size),
            'VolumeMountDirectories': ('"%s"' % '" "'.join(mount_dirs)) if mount_dirs else '',
            'DockerDataRootDirectory': docker_config['dataRoot'],
            'DockerImage': docker_config.get('image', ''),
            'DockerfilePath': docker_config.get('file', ''),
            'DockerNvidiaRuntime': 'true' if is_gpu_instance(instance_type) else 'false',
            'DockerWorkingDirectory': docker_config['workingDir'],
            'ProjectS3Bucket': bucket_name,
            'ProjectDirectory': remote_project_dir,
        }

        res = self._cf.create_stack(
            StackName=self._stack_name,
            TemplateBody=template,
            Parameters=[{'ParameterKey': key, 'ParameterValue': value} for key, value in params.items()],
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DO_NOTHING',
        )

        return res

    def delete_stack(self):
        self._cf.delete_stack(StackName=self._stack_name)
