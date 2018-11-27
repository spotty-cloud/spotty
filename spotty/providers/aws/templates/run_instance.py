from collections import OrderedDict
import yaml
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.helpers.instance_config import InstanceConfig
from spotty.providers.aws.helpers.volume_config import VolumeConfig
from spotty.providers.aws.utils import data_dir
from spotty.providers.aws.validation import is_gpu_instance


class RunInstanceTemplate(object):

    def __init__(self, instance_config: InstanceConfig):
        self._config = instance_config

    def prepare(self, output: AbstractOutputWriter):
        """Prepares CloudFormation template to run a Spot Instance."""

        # read and update CF template
        with open(data_dir('run_container.yaml')) as f:
            template = yaml.load(f, Loader=CfnYamlLoader)

        # get volume resources and updated availability zone
        volume_resources = self._get_volume_resources(output)

        # add volume resources to the template
        template['Resources'].update(volume_resources)

        # set availability zone
        availability_zone = self._config.get_volumes_az()
        if availability_zone:
            template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['Placement'] = {
                'AvailabilityZone': availability_zone,
            }
            output.write('- availability zone: %s' % availability_zone)
        else:
            output.write('- availability zone: auto')

        # set subnet
        if self._config.subnet_id:
            template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['NetworkInterfaces'] = [{
                'SubnetId': self._config.subnet_id,
                'DeviceIndex': 0,
                'Groups': template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['SecurityGroupIds'],
            }]
            del template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['SecurityGroupIds']

        # add ports to the security group
        for port in self._config.container.ports:
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

        if self._config.on_demand:
            # run on-demand instance
            del template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['InstanceMarketOptions']
            output.write('- on-demand instance')
        else:
            # set maximum price
            if self._config.max_price:
                template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData'] \
                    ['InstanceMarketOptions']['SpotOptions']['MaxPrice'] = self._config.max_price

            output.write('- maximum Spot Instance price: %s'
                         % (('%.04f' % self._config.max_price) if self._config.max_price else 'on-demand'))

        # set initial docker commands
        if self._config.container.commands:
            template['Resources']['SpotInstanceLaunchTemplate']['Metadata']['AWS::CloudFormation::Init'] \
                ['docker_container_config']['files']['/tmp/docker/docker_commands.sh']['content'] = self._config.container.commands

        return yaml.dump(template, Dumper=CfnYamlDumper)

    def get_parameters(self, instance_profile_arn: str, bucket_name: str, dry_run=False):
        # get VPC ID
        vpc_id = self._config.get_vpc_id()

        # get image info
        ami = self._config.get_ami()
        if not ami:
            raise ValueError('AMI with name "%s" not found.\n'
                             'Use "spotty aws create-ami" command to create an AMI with NVIDIA Docker.' % ami.name)

        # check root volume size
        root_volume_size = self._config.root_volume_size
        if root_volume_size and root_volume_size < ami.size:
            raise ValueError('Root volume size cannot be less than the size of AMI (%dGB).' % ami.size)
        elif not root_volume_size:
            # if a root volume size is not specified, make it 5GB larger than the AMI size
            root_volume_size = ami.size + 5

        # create key pair
        key_name = self._config.key_pair.create_key(dry_run)

        # split container volumes mapping to two different lists
        docker_host_dirs = []
        docker_container_dirs = []
        for volume_mount in self._config.volume_mounts:
            docker_host_dirs.append(volume_mount.host_dir)
            docker_container_dirs.append(volume_mount.container_dir)

        # get mount directories for the volumes
        mount_dirs = OrderedDict([(volume.name, volume.mount_dir) for volume in self._config.volumes])

        # create stack
        parameters = {
            'VpcId': vpc_id,
            'InstanceProfileArn': instance_profile_arn,
            'InstanceType': self._config.instance_type,
            'KeyName': key_name,
            'ImageId': ami.image_id,
            'RootVolumeSize': str(root_volume_size),
            'VolumeMountDirectories': ('"%s"' % '" "'.join(mount_dirs)) if mount_dirs else '',
            'DockerDataRootDirectory': self._config.docker_data_root,
            'DockerImage': self._config.container.image,
            'DockerfilePath': self._config.dockerfile_path,
            'DockerBuildContextPath': self._config.docker_context_path,
            'DockerNvidiaRuntime': 'true' if is_gpu_instance(self._config.instance_type) else 'false',
            'DockerWorkingDirectory': self._config.container.working_dir,
            'DockerVolumesHostDirs': ('"%s"' % '" "'.join(docker_host_dirs)) if docker_host_dirs else '',
            'DockerVolumesContainerDirs': ('"%s"' % '" "'.join(docker_container_dirs)) if docker_container_dirs else '',
            'InstanceNameTag': self._config.ec2_instance_name,
            'ProjectS3Bucket': bucket_name,
            'HostProjectDirectory': self._config.host_project_dir,
        }

        return parameters

    def _get_volume_attachment_resource(self, volume_id, device_name):
        attachment_resource = {
            'Type': 'AWS::EC2::VolumeAttachment',
            'Properties': {
                'Device': device_name,
                'InstanceId': {'Ref': 'SpotInstance'},
                'VolumeId': volume_id,
            },
        }

        return attachment_resource

    def _get_volume_resource(self, volume: VolumeConfig, output: AbstractOutputWriter):
        # new volume will be created
        volume_resource = {
            'Type': 'AWS::EC2::Volume',
            'DeletionPolicy': 'Retain',
            'Properties': {
                'AvailabilityZone': {'Fn::GetAtt': ['SpotInstance', 'AvailabilityZone']},
                'Tags': [{
                    'Key': 'Name',
                    'Value': volume.ec2_volume_name,
                }],
            },
        }

        # check if the snapshot exists and restore the volume from it
        snapshot = volume.get_snapshot()
        if snapshot:
            # volume will be restored from the snapshot
            # check size of the volume
            if volume.size and (volume.size < snapshot.size):
                raise ValueError('Specified size for the "%s" volume (%dGB) is less than size of the '
                                 'snapshot (%dGB).'
                                 % (volume.name, volume.size, snapshot.size))

            # set snapshot ID
            volume_resource['Properties']['SnapshotId'] = snapshot.snapshot_id

            output.write('- volume "%s" will be restored from the snapshot "%s"'
                         % (volume.ec2_volume_name, snapshot.name))

        else:
            # empty volume will be created, check that the size is specified
            if not volume.size:
                raise ValueError('Size for the new volume is required.')

            # if the snapshot was explicitly specified and it doesn't exist, raise an error
            if volume.snapshot_name:
                raise ValueError('Snapshot "%s" doesn\'t exist' % volume.snapshot_name)

            output.write('- volume "%s" will be created' % volume.ec2_volume_name)

        # set size of the volume
        if volume.size:
            volume_resource['Properties']['Size'] = volume.size

        # set a name for the new volume
        volume_resource['Properties']['Tags'] = [{'Key': 'Name', 'Value': volume.ec2_volume_name}]

        return volume_resource

    def _get_volume_resources(self, output: AbstractOutputWriter):
        resources = {}

        # ending letters for the devices (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html)
        # TODO: different device names on Nitro-based instances,
        # see: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvme-ebs-volumes.html
        device_letters = 'fghijklmnop'

        # create and attach volumes
        for i, volume in enumerate(self._config.volumes):
            device_letter = device_letters[i]

            ec2_volume = volume.get_ec2_volume()
            if ec2_volume:
                # check size of the volume
                if volume.size and (volume.size != ec2_volume.size):
                    raise ValueError('Specified size for the "%s" volume (%dGB) doesn\'t match the size of the '
                                     'existing volume (%dGB).' % (volume.name, volume.size, ec2_volume.size))

                output.write('- volume "%s" (%s) will be attached' % (ec2_volume.name, ec2_volume.volume_id))

                volume_id = ec2_volume.volume_id
            else:
                # create Volume resource
                vol_resource_name = 'Volume' + device_letter.upper()
                vol_resource = self._get_volume_resource(volume, output)
                resources[vol_resource_name] = vol_resource

                volume_id = {'Ref': vol_resource_name}

            # create VolumeAttachment resource
            vol_attachment_resource_name = 'VolumeAttachment' + device_letter.upper()
            device_name = '/dev/sd' + device_letter
            vol_attachment_resource = self._get_volume_attachment_resource(volume_id, device_name)
            resources[vol_attachment_resource_name] = vol_attachment_resource

        return resources
