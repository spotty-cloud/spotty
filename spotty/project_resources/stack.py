import yaml
from botocore.exceptions import EndpointConnectionError
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.helpers.resources import get_snapshot, is_gpu_instance, stack_exists
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
        return stack_exists(self._cf, self._stack_name)

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
        for i, volume in enumerate(volumes):
            device_letter = device_letters[i]
            volume_resource_name = 'Volume' + device_letter.upper()
            attachment_resource_name = 'VolumeAttachment' + device_letter.upper()

            volume_resource = {
                'Type': 'AWS::EC2::Volume',
                'Properties': {
                    'AvailabilityZone': {'Fn::GetAtt': ['SpotInstance', 'AvailabilityZone']},
                },
            }

            attachment_resource = {
                'Type': 'AWS::EC2::VolumeAttachment',
                'Properties': {
                    'Device': '/dev/sd' + device_letter,
                    'InstanceId': {'Ref': 'SpotInstance'},
                    'VolumeId': {'Ref': volume_resource_name},
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
                        output.write('  - size of the "%s" snapshot will be increased from %dGB to %dGB'
                                     % (snapshot_name, snapshot_info['VolumeSize'], volume_size))

                # set snapshot ID
                orig_snapshot_id = snapshot_info['SnapshotId']
                volume_resource['Properties']['SnapshotId'] = orig_snapshot_id

                # rename or delete the original snapshot on stack deletion
                if deletion_policy == 'create_snapshot':
                    # rename the original snapshot once new snapshot is created
                    s_renaming_resource_name = 'RenameSnapshot' + device_letter.upper()
                    template['Resources'][s_renaming_resource_name] = {
                        'Type': 'Custom::SnapshotRenaming',
                        'Properties': {
                            'ServiceToken': {'Fn::GetAtt': ['RenameSnapshotFunction', 'Arn']},
                            'SnapshotId': orig_snapshot_id,
                        },
                    }
                    volume_resource['DependsOn'] = s_renaming_resource_name

                    # make sure that the lambda to update log group retention was called after the log group was created
                    template['Resources']['RenameSnapshotFunctionRetention']['DependsOn'] += [s_renaming_resource_name]

                elif deletion_policy == 'update_snapshot':
                    # delete the original snapshot once new snapshot is created
                    s_deletion_resource_name = 'DeleteSnapshot' + device_letter.upper()
                    template['Resources'][s_deletion_resource_name] = {
                        'Type': 'Custom::SnapshotDeletion',
                        'Properties': {
                            'ServiceToken': {'Fn::GetAtt': ['DeleteSnapshotFunction', 'Arn']},
                            'SnapshotId': orig_snapshot_id,
                        },
                    }
                    volume_resource['DependsOn'] = s_deletion_resource_name

                    # make sure that the lambda to update log group retention was called after the log group was created
                    template['Resources']['DeleteSnapshotFunctionRetention']['DependsOn'] += [s_deletion_resource_name]

            # set size of the volume
            if volume_size:
                volume_resource['Properties']['Size'] = volume_size

            # set tag for new volume (future snapshot name)
            if snapshot_name:
                volume_resource['Properties']['Tags'] = [{'Key': 'Name', 'Value': snapshot_name}]

            if deletion_policy == 'delete':
                # delete the volume on termination
                volume_resource['DeletionPolicy'] = 'Delete'
            elif deletion_policy in ['create_snapshot', 'update_snapshot']:
                # create snapshots on termination
                volume_resource['DeletionPolicy'] = 'Snapshot'

            # instance termination lambda should depend on all volume attachments
            template['Resources']['TerminateInstance']['DependsOn'] += [attachment_resource_name]

            # add volume resources to the template
            template['Resources'][volume_resource_name] = volume_resource
            template['Resources'][attachment_resource_name] = attachment_resource

        # delete log group retention lambda calls
        if not template['Resources']['DeleteSnapshotFunctionRetention']['DependsOn']:
            del template['Resources']['DeleteSnapshotFunctionRetention']

        if not template['Resources']['RenameSnapshotFunctionRetention']['DependsOn']:
            del template['Resources']['RenameSnapshotFunctionRetention']

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

    def create_stack(self, ec2, template: str, instance_profile_arn: str, instance_type: str, ami_name: str,
                     root_volume_size: int, mount_dirs: list, bucket_name: str, remote_project_dir: str,
                     docker_config: dict):
        # get default VPC ID
        res = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        if not len(res['Vpcs']):
            raise ValueError('Default VPC not found')

        vpc_id = res['Vpcs'][0]['VpcId']

        # get image info
        ami_info = ec2.describe_images(Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])
        if not len(ami_info['Images']):
            raise ValueError('AMI with name "%s" not found.\n'
                             'Use "spotty create-ami" command to create an AMI with NVIDIA Docker.' % ami_name)

        ami_id = ami_info['Images'][0]['ImageId']

        # check root volume size
        image_volume_size = ami_info['Images'][0]['BlockDeviceMappings'][0]['Ebs']['VolumeSize']
        if root_volume_size and root_volume_size < image_volume_size:
            raise ValueError('Root volume size cannot be less than the size of AMI (%dGB).' % image_volume_size)
        elif not root_volume_size:
            root_volume_size = image_volume_size + 5

        # create key pair
        project_key = KeyPairResource(ec2, self._project_name, self._region)
        key_name = project_key.create_key()

        # create stack
        params = {
            'VpcId': vpc_id,
            'InstanceProfileArn': instance_profile_arn,
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
