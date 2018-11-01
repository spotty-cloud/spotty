import os
import boto3
import yaml
from botocore.exceptions import EndpointConnectionError
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.providers.aws.helpers.resources import get_snapshot, is_gpu_instance, stack_exists, get_volume
from spotty.providers.aws.helpers.spot_prices import get_current_spot_price
from spotty.providers.aws.project_resources.key_pair import KeyPairResource
from spotty.utils import data_dir


class InstanceStackResource(object):

    def __init__(self, project_name: str, region: str):
        self._cf = boto3.client('cloudformation', region_name=region)
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
        # TODO: remove catching?
        except EndpointConnectionError:
            res = {}

        return res['Stacks'][0]

    def prepare_template(self, ec2, project_name: str, instance_name: str, availability_zone: str, instance_type: str,
                         volumes: list, ports: list, max_price, docker_commands):
        """Prepares CloudFormation template to run a Spot Instance."""

        # read and update CF template
        with open(data_dir('run_container.yaml')) as f:
            template = yaml.load(f, Loader=CfnYamlLoader)

        # ending letters for the devices (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html)
        device_letters = 'fghijklmnop'

        # create and attach volumes
        for i, volume in enumerate(volumes):
            device_letter = device_letters[i]
            volume_resources, volume_availability_zone = self._get_volume_resources(ec2, project_name, instance_name,
                                                                                    volume, device_letter)

            # existing volume will be attached to the instance
            if availability_zone and volume_availability_zone and (availability_zone != volume_availability_zone):
                raise ValueError('You have two existing volumes in different availability zones or an availability '
                                 'zone in the configuration file doesn\'t match an availability zone of the '
                                 'existing volume.')

            # update availability zone
            if volume_availability_zone:
                availability_zone = volume_availability_zone

            # update template resources
            template['Resources'].update(volume_resources)

        # set availability zone
        if availability_zone:
            template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['Placement'] = {
                'AvailabilityZone': availability_zone,
            }

        # make sure that the lambda to update log group retention was called after
        # the log group was created
        template['Resources']['RenameSnapshotFunctionRetention']['DependsOn'] = [
            resource_name for resource_name, resource in template['Resources'].items()
            if resource['Type'] == 'Custom::SnapshotRenaming'
        ]

        # delete calls of the SetLogsRetentionFunction lambda
        if not template['Resources']['RenameSnapshotFunctionRetention']['DependsOn']:
            del template['Resources']['RenameSnapshotFunctionRetention']

        # make sure that the lambda to update log group retention was called after
        # the log group was created
        template['Resources']['DeleteSnapshotFunctionRetention']['DependsOn'] = [
            resource_name for resource_name, resource in template['Resources'].items()
            if resource['Type'] == 'Custom::SnapshotDeletion'
        ]

        # delete calls of the SetLogsRetentionFunction lambda
        if not template['Resources']['DeleteSnapshotFunctionRetention']['DependsOn']:
            del template['Resources']['DeleteSnapshotFunctionRetention']

        # TerminateInstanceFunction lambda should depend on all volume attachments
        template['Resources']['TerminateInstance']['DependsOn'] = [
            resource_name for resource_name, resource in template['Resources'].items()
            if resource['Type'] == 'AWS::EC2::VolumeAttachment'
        ]

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

        if max_price:
            # check the maximum price
            current_price = get_current_spot_price(ec2, instance_type, availability_zone)
            if current_price > max_price:
                raise ValueError('Current price for the instance (%.04f) is higher than the maximum price in the '
                                 'configuration file (%.04f).' % (current_price, max_price))

            # set maximum price
            template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData'] \
                ['InstanceMarketOptions']['SpotOptions']['MaxPrice'] = max_price

        # set initial docker commands
        if docker_commands:
            template['Resources']['SpotInstanceLaunchTemplate']['Metadata']['AWS::CloudFormation::Init'] \
                ['docker_container_config']['files']['/tmp/docker/docker_commands.sh']['content'] = docker_commands

        return yaml.dump(template, Dumper=CfnYamlDumper)

    def create_stack(self, ec2, template: str, instance_profile_arn: str, instance_type: str, ami_name: str,
                     root_volume_size: int, project_dir: str, mount_dirs: list, container_volumes: dict,
                     bucket_name: str, container_config: dict):
        """Runs CloudFormation template."""

        # container_config['projectDir']

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
                             'Use "spotty aws create-ami" command to create an AMI with NVIDIA Docker.' % ami_name)

        ami_id = ami_info['Images'][0]['ImageId']

        # check root volume size
        image_volume_size = ami_info['Images'][0]['BlockDeviceMappings'][0]['Ebs']['VolumeSize']
        if root_volume_size and root_volume_size < image_volume_size:
            raise ValueError('Root volume size cannot be less than the size of AMI (%dGB).' % image_volume_size)
        elif not root_volume_size:
            root_volume_size = image_volume_size + 5

        # create key pair
        project_key = KeyPairResource(self._project_name, self._region)
        key_name = project_key.create_key()

        # working directory for the Docker container
        working_dir = container_config['workingDir']
        if not working_dir:
            working_dir = container_config['projectDir']

        # get the Dockerfile path and the build's context path
        dockerfile_path = container_config.get('file', '')
        if not os.path.isabs(dockerfile_path):
            dockerfile_path = container_config['projectDir'] + '/' + dockerfile_path

        docker_context_path = ''
        if dockerfile_path:
            docker_context_path = os.path.dirname(dockerfile_path)

        # split container volumes mapping to two different lists
        docker_host_dirs = []
        docker_container_dirs = []
        for host_dir, container_dir in container_volumes.items():
            docker_host_dirs.append(host_dir)
            docker_container_dirs.append(container_dir)

        # create stack
        params = {
            'VpcId': vpc_id,
            'InstanceProfileArn': instance_profile_arn,
            'InstanceType': instance_type,
            'KeyName': key_name,
            'ImageId': ami_id,
            'RootVolumeSize': str(root_volume_size),
            'VolumeMountDirectories': ('"%s"' % '" "'.join(mount_dirs)) if mount_dirs else '',
            'DockerDataRootDirectory': container_config['dataRoot'],
            'DockerImage': container_config.get('image', ''),
            'DockerfilePath': dockerfile_path,
            'DockerBuildContextPath': docker_context_path,
            'DockerNvidiaRuntime': 'true' if is_gpu_instance(instance_type) else 'false',
            'DockerWorkingDirectory': working_dir,
            'DockerVolumesHostDirs': ('"%s"' % '" "'.join(docker_host_dirs)) if docker_host_dirs else '',
            'DockerVolumesContainerDirs': ('"%s"' % '" "'.join(docker_container_dirs)) if docker_container_dirs else '',
            'ProjectS3Bucket': bucket_name,
            'ProjectDirectory': project_dir,
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

    @staticmethod
    def _get_volume_resources(ec2, project_name: str, instance_name: str, volume_config: dict, device_letter: str):
        resources = {}
        availability_zone = ''

        # VolumeAttachment resource
        attachment_resource_name = 'VolumeAttachment' + device_letter.upper()
        attachment_resource = {
            'Type': 'AWS::EC2::VolumeAttachment',
            'Properties': {
                'Device': '/dev/sd' + device_letter,
                'InstanceId': {'Ref': 'SpotInstance'},
            },
        }

        volume_name = '%s-%s-%s' % (project_name, volume_config['name'], instance_name)
        volume_params = volume_config['parameters']
        volume_size = volume_params['size']
        volume_snapshot_name = volume_params['snapshotName']
        deletion_policy = volume_params['deletionPolicy']

        # check that the volume name is specified
        if not volume_name and deletion_policy != 'delete':
            raise ValueError('Volume name is required if the deletion policy isn\'t set to "delete".')

        volume_info = get_volume(ec2, volume_name) if volume_name else {}
        if volume_info:
            # set availability zone
            availability_zone = volume_info['AvailabilityZone']

            # set volume ID for the VolumeAttachment resource
            attachment_resource['Properties']['VolumeId'] = volume_info['VolumeId']

            # check size of the volume
            if volume_size and (volume_size != volume_info['Size']):
                raise ValueError('Specified size for the "%s" volume (%dGB) doesn\'t match the size of the '
                                 'existing volume (%dGB).' % (volume_name, volume_size, volume_info['Size']))
        else:
            # new volume will be created
            volume_resource_name = 'Volume' + device_letter.upper()
            volume_resource = {
                'Type': 'AWS::EC2::Volume',
                'Properties': {
                    'AvailabilityZone': {'Fn::GetAtt': ['SpotInstance', 'AvailabilityZone']},
                },
            }

            # update VolumeAttachment resource with the reference to new volume
            attachment_resource['Properties']['VolumeId'] = {'Ref': volume_resource_name}

            # check if the snapshot exists
            snapshot_name = volume_snapshot_name if volume_snapshot_name else volume_name
            snapshot_info = get_snapshot(ec2, snapshot_name) if volume_name else {}
            if snapshot_info:
                # volume will be restored from the snapshot
                # check size of the volume
                if volume_size and (volume_size < snapshot_info['VolumeSize']):
                    raise ValueError('Specified size for the "%s" volume (%dGB) is less than size of the '
                                     'snapshot (%dGB).'
                                     % (volume_name, volume_size, snapshot_info['VolumeSize']))

                # set snapshot ID
                orig_snapshot_id = snapshot_info['SnapshotId']
                volume_resource['Properties']['SnapshotId'] = orig_snapshot_id

                # rename or delete the original snapshot on stack deletion
                if deletion_policy == 'create_snapshot':
                    # rename the original snapshot once new snapshot is created
                    s_renaming_resource_name = 'RenameSnapshot' + device_letter.upper()
                    resources[s_renaming_resource_name] = {
                        'Type': 'Custom::SnapshotRenaming',
                        'Properties': {
                            'ServiceToken': {'Fn::GetAtt': ['RenameSnapshotFunction', 'Arn']},
                            'SnapshotId': orig_snapshot_id,
                        },
                    }
                    volume_resource['DependsOn'] = s_renaming_resource_name

                elif deletion_policy == 'update_snapshot':
                    # delete the original snapshot once new snapshot is created
                    s_deletion_resource_name = 'DeleteSnapshot' + device_letter.upper()
                    resources[s_deletion_resource_name] = {
                        'Type': 'Custom::SnapshotDeletion',
                        'Properties': {
                            'ServiceToken': {'Fn::GetAtt': ['DeleteSnapshotFunction', 'Arn']},
                            'SnapshotId': orig_snapshot_id,
                        },
                    }
                    volume_resource['DependsOn'] = s_deletion_resource_name
            else:
                # empty volume will be created, check that the size is specified
                if not volume_size:
                    raise ValueError('Size for the new volume is required.')

                # if the snapshot explicitly specified and it doesn't exist, raise an error
                if volume_snapshot_name:
                    raise ValueError('Snapshot "%s" doesn\'t exist' % volume_snapshot_name)

            # set size of the volume
            if volume_size:
                volume_resource['Properties']['Size'] = volume_size

            # set the Name tag for new volume (it's the future snapshot name as well)
            if volume_name:
                volume_resource['Properties']['Tags'] = [{'Key': 'Name', 'Value': volume_name}]

            if deletion_policy in ['create_snapshot', 'update_snapshot']:
                # create snapshots on termination
                volume_resource['DeletionPolicy'] = 'Snapshot'
            elif deletion_policy == 'retain':
                # retain the volume on termination
                volume_resource['DeletionPolicy'] = 'Retain'
            elif deletion_policy == 'delete':
                # delete the volume on termination
                volume_resource['DeletionPolicy'] = 'Delete'

            # update resources
            resources[volume_resource_name] = volume_resource

        # update resources
        resources[attachment_resource_name] = attachment_resource

        return resources, availability_zone
