from typing import List
import os
import yaml
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.deployment.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deployment.project_resources.ebs_volume import EbsVolume


def prepare_instance_template(instance_config: InstanceConfig, volumes: List[AbstractInstanceVolume],
                              availability_zone: str, container: ContainerDeployment, output: AbstractOutputWriter):
    """Prepares CloudFormation template to run a Spot Instance."""

    # read and update CF template
    with open(os.path.join(os.path.dirname(__file__), 'data', 'instance.yaml')) as f:
        template = yaml.load(f, Loader=CfnYamlLoader)

    # get volume resources and updated availability zone
    volume_resources = _get_volume_resources(volumes, output)

    # add volume resources to the template
    template['Resources'].update(volume_resources)

    # set availability zone
    if availability_zone:
        template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['Placement'] = {
            'AvailabilityZone': availability_zone,
        }
        output.write('- availability zone: %s' % availability_zone)
    else:
        output.write('- availability zone: auto')

    # set subnet
    if instance_config.subnet_id:
        template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['NetworkInterfaces'] = [
            {
                'SubnetId': instance_config.subnet_id,
                'DeviceIndex': 0,
                'Groups': template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
                    'SecurityGroupIds'],
            }]
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['SecurityGroupIds']

    # add ports to the security group
    for port in container.config.ports:
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

    if instance_config.on_demand:
        # run on-demand instance
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
            'InstanceMarketOptions']
        output.write('- on-demand instance')
    else:
        # set maximum price
        if instance_config.max_price:
            template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'] \
                ['InstanceMarketOptions']['SpotOptions']['MaxPrice'] = instance_config.max_price

        output.write('- maximum Spot Instance price: %s'
                     % (('%.04f' % instance_config.max_price) if instance_config.max_price else 'on-demand'))

    # set initial docker commands
    if container.config.commands:
        template['Resources']['InstanceLaunchTemplate']['Metadata']['AWS::CloudFormation::Init'] \
            ['docker_container_config']['files']['/tmp/spotty/container/scripts/startup_commands.sh']['content'] \
            = container.config.commands

    return yaml.dump(template, Dumper=CfnYamlDumper)


def _get_volume_attachment_resource(volume_id, device_name):
    attachment_resource = {
        'Type': 'AWS::EC2::VolumeAttachment',
        'Properties': {
            'Device': device_name,
            'InstanceId': {'Ref': 'Instance'},
            'VolumeId': volume_id,
        },
    }

    return attachment_resource


def _get_volume_resource(volume: EbsVolume, output: AbstractOutputWriter):
    # new volume will be created
    volume_resource = {
        'Type': 'AWS::EC2::Volume',
        'DeletionPolicy': 'Retain',
        'Properties': {
            'AvailabilityZone': {'Fn::GetAtt': ['Instance', 'AvailabilityZone']},
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

        output.write('- volume "%s" will be restored from the snapshot' % volume.ec2_volume_name)

    else:
        # empty volume will be created, check that the size is specified
        if not volume.size:
            raise ValueError('Size for the new volume is required.')

        output.write('- volume "%s" will be created' % volume.ec2_volume_name)

    # set size of the volume
    if volume.size:
        volume_resource['Properties']['Size'] = volume.size

    # set a name for the new volume
    volume_resource['Properties']['Tags'] = [{'Key': 'Name', 'Value': volume.ec2_volume_name}]

    return volume_resource


def _get_volume_resources(volumes: List[AbstractInstanceVolume], output: AbstractOutputWriter):
    resources = {}

    # ending letters for the devices (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html)
    # TODO: different device names on Nitro-based instances,
    # see: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvme-ebs-volumes.html
    device_letters = 'fghijklmnop'

    # create and attach volumes
    for i, volume in enumerate(volumes):
        if isinstance(volume, EbsVolume):
            device_letter = device_letters[i]

            ec2_volume = volume.get_ec2_volume()
            if ec2_volume:
                # check if the volume is available
                if not ec2_volume.is_available():
                    raise ValueError('EBS volume "%s" is not available.' % volume.ec2_volume_name)

                # check size of the volume
                if volume.size and (volume.size != ec2_volume.size):
                    raise ValueError('Specified size for the "%s" volume (%dGB) doesn\'t match the size of the '
                                     'existing volume (%dGB).' % (volume.name, volume.size, ec2_volume.size))

                output.write('- volume "%s" (%s) will be attached' % (ec2_volume.name, ec2_volume.volume_id))

                volume_id = ec2_volume.volume_id
            else:
                # create Volume resource
                vol_resource_name = 'Volume' + device_letter.upper()
                vol_resource = _get_volume_resource(volume, output)
                resources[vol_resource_name] = vol_resource

                volume_id = {'Ref': vol_resource_name}

            # create VolumeAttachment resource
            vol_attachment_resource_name = 'VolumeAttachment' + device_letter.upper()
            device_name = '/dev/sd' + device_letter
            vol_attachment_resource = _get_volume_attachment_resource(volume_id, device_name)
            resources[vol_attachment_resource_name] = vol_attachment_resource

    return resources
