from typing import List
import os
import chevron
import yaml
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.tmp_dir_volume import TmpDirVolume
from spotty.config.validation import is_subdir
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container.docker.docker_commands import DockerCommands
from spotty.deployment.container.docker.scripts.container_bash_script import ContainerBashScript
from spotty.deployment.abstract_cloud_instance.file_structure import INSTANCE_SPOTTY_TMP_DIR, \
    CONTAINER_BASH_SCRIPT_PATH, \
    INSTANCE_STARTUP_SCRIPTS_DIR, CONTAINERS_TMP_DIR
from spotty.providers.aws.cfn_templates.instance.start_container_script import StartContainerScriptWithCfnSignals
from spotty.providers.aws.helpers.ami import get_ami
from spotty.providers.aws.helpers.vpc import get_vpc_id
from spotty.providers.aws.resources.snapshot import Snapshot
from spotty.providers.aws.resources.volume import Volume
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.config.ebs_volume import EbsVolume
from spotty.providers.aws.helpers.logs import get_logs_s3_path


def prepare_instance_template(ec2, instance_config: InstanceConfig, docker_commands: DockerCommands,
                              availability_zone: str, sync_project_cmd: str, output: AbstractOutputWriter):
    """Prepares CloudFormation template to run a Spot Instance."""

    # read and update CF template
    with open(os.path.join(os.path.dirname(__file__), 'data', 'template.yaml')) as f:
        template = yaml.load(f, Loader=CfnYamlLoader)

    # get volume resources and updated availability zone
    volume_resources = _get_volume_resources(ec2, instance_config.volumes, output)

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
    for port in instance_config.ports:
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

    if instance_config.is_spot_instance:
        # set maximum price
        if instance_config.max_price:
            template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'] \
                ['InstanceMarketOptions']['SpotOptions']['MaxPrice'] = instance_config.max_price

        output.write('- maximum Spot Instance price: %s'
                     % (('%.04f' % instance_config.max_price) if instance_config.max_price else 'on-demand'))
    else:
        # run on-demand instance
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
            'InstanceMarketOptions']
        output.write('- on-demand instance')

    # set the user data script
    template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['UserData'] = {
        'Fn::Base64': {
            'Fn::Sub': _read_template_file(os.path.join('startup_scripts', 'user_data.sh')),
        },
    }

    # run sync command as a non-root user
    if instance_config.container_config.run_as_host_user:
        sync_project_cmd = 'sudo -u %s %s' % (instance_config.user, sync_project_cmd)

    # get mount directories
    mount_dirs = [volume.mount_dir for volume in instance_config.volumes if isinstance(volume, EbsVolume)]

    # set CloudFormation configs
    cfn_init_configs = [
        {
            'name': 'prepare_instance',
            'files': {
                INSTANCE_STARTUP_SCRIPTS_DIR + '/01_prepare_instance.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': {
                        'Fn::Sub': _read_template_file(os.path.join('startup_scripts', '01_prepare_instance.sh'), {
                            'CONTAINER_BASH_SCRIPT_PATH': CONTAINER_BASH_SCRIPT_PATH,
                            'SPOTTY_TMP_DIR': INSTANCE_SPOTTY_TMP_DIR,
                            'CONTAINERS_TMP_DIR': CONTAINERS_TMP_DIR,
                        }),
                    },
                },
                CONTAINER_BASH_SCRIPT_PATH: {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': ContainerBashScript(docker_commands).render(),
                },
                '/home/ubuntu/.tmux.conf': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000644',
                    'content': {
                        'Fn::Sub': _read_template_file(os.path.join('files', 'tmux.conf')),
                    },
                },
            },
            'command': INSTANCE_STARTUP_SCRIPTS_DIR + '/01_prepare_instance.sh',
        },
        {
            'name': 'mount_volumes',
            'files': {
                INSTANCE_STARTUP_SCRIPTS_DIR + '/02_mount_volumes.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': {
                        'Fn::Sub': _read_template_file(os.path.join('startup_scripts', '02_mount_volumes.sh'), {
                            'MOUNT_DIRS': ('"%s"' % '" "'.join(mount_dirs)) if mount_dirs else '',
                            'TMP_VOLUME_DIRS': [{'PATH': volume.host_path} for volume in instance_config.volumes
                                                if isinstance(volume, TmpDirVolume)],
                        }),
                    },
                },
            },
            'command': INSTANCE_STARTUP_SCRIPTS_DIR + '/02_mount_volumes.sh',
        },
        {
            'name': 'set_docker_root',
            'files': {
                INSTANCE_STARTUP_SCRIPTS_DIR + '/03_set_docker_root.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': {
                        'Fn::Sub': _read_template_file(os.path.join('startup_scripts', '03_set_docker_root.sh')),
                    },
                },
            },
            'command': INSTANCE_STARTUP_SCRIPTS_DIR + '/03_set_docker_root.sh',
        },
        {
            'name': 'sync_project',
            'files': {
                INSTANCE_STARTUP_SCRIPTS_DIR + '/04_sync_project.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': {
                        'Fn::Sub': _read_template_file(os.path.join('startup_scripts', '04_sync_project.sh'), {
                            'SYNC_PROJECT_CMD': sync_project_cmd,
                        }),
                    },
                },
            },
            'command': INSTANCE_STARTUP_SCRIPTS_DIR + '/04_sync_project.sh',
        },
        {
            'name': 'run_instance_startup_commands',
            'files': {
                INSTANCE_STARTUP_SCRIPTS_DIR + '/05_run_instance_startup_commands.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': {
                        'Fn::Sub': _read_template_file(
                            os.path.join('startup_scripts', '05_run_instance_startup_commands.sh'), {
                                'INSTANCE_STARTUP_SCRIPTS_DIR': INSTANCE_STARTUP_SCRIPTS_DIR,
                            }),
                    },
                },
                INSTANCE_STARTUP_SCRIPTS_DIR + '/instance_startup_commands.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000644',
                    'content': instance_config.commands or '#',
                },
            },
            'command': INSTANCE_STARTUP_SCRIPTS_DIR + '/05_run_instance_startup_commands.sh',
        },
        {
            'name': 'start_container',
            'files': {
                INSTANCE_STARTUP_SCRIPTS_DIR + '/06_start_container.sh': {
                    'owner': 'ubuntu',
                    'group': 'ubuntu',
                    'mode': '000755',
                    'content': {
                        'Fn::Sub': StartContainerScriptWithCfnSignals(docker_commands).render(print_trace=True),
                    },
                },
            },
            'command': INSTANCE_STARTUP_SCRIPTS_DIR + '/06_start_container.sh',
        },
    ]

    template['Resources']['InstanceLaunchTemplate']['Metadata']['AWS::CloudFormation::Init']['configSets'] = {
        'init': [config['name'] for config in cfn_init_configs],
    }

    for config in cfn_init_configs:
        template['Resources']['InstanceLaunchTemplate']['Metadata']['AWS::CloudFormation::Init'][config['name']] = {
            'files': config.get('files', {}),
            'commands': {
                config['name']: {
                    'command': config['command'],
                }
            },
        }

    return yaml.dump(template, Dumper=CfnYamlDumper)


def _read_template_file(filename: str, params: dict = None):
    with open(os.path.join(os.path.dirname(__file__), 'data', filename)) as f:
        content = f.read()

    if params:
        content = chevron.render(content, params)

    return content


def _get_volume_attachment_resource(volume_id, device_name):
    attachment_resource = {
        'Type': 'AWS::EC2::VolumeAttachment',
        'Properties': {
            'Device': device_name,
            'InstanceId': {'Ref': 'Instance'},
            'VolumeId': volume_id if isinstance(volume_id, str) else dict(volume_id),  # avoid YAML aliases
        },
        'Metadata': {
            'Device': device_name,
            'VolumeId': volume_id if isinstance(volume_id, str) else dict(volume_id),  # avoid YAML aliases
        },
    }

    return attachment_resource


def _get_volume_resource(ec2, volume: EbsVolume, output: AbstractOutputWriter):
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
            'VolumeType': volume.type,
        },
    }

    # check if the snapshot exists and restore the volume from it
    snapshot = Snapshot.get_by_name(ec2, volume.ec2_volume_name)
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


def _get_volume_resources(ec2, volumes: List[AbstractInstanceVolume], output: AbstractOutputWriter):
    resources = {}

    # ending letters for the devices (see: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html)
    device_letters = 'fghijklmnop'

    # create and attach volumes
    for i, volume in enumerate(volumes):
        if isinstance(volume, EbsVolume):
            device_letter = device_letters[i]

            ec2_volume = Volume.get_by_name(ec2, volume.ec2_volume_name)
            if ec2_volume:
                # check if the volume is available
                if not ec2_volume.is_available():
                    raise ValueError('EBS volume "%s" is not available (state: %s).'
                                     % (volume.ec2_volume_name, ec2_volume.state))

                # check size of the volume
                if volume.size and (volume.size != ec2_volume.size):
                    raise ValueError('Specified size for the "%s" volume (%dGB) doesn\'t match the size of the '
                                     'existing volume (%dGB).' % (volume.name, volume.size, ec2_volume.size))

                output.write('- volume "%s" (%s) will be attached' % (ec2_volume.name, ec2_volume.volume_id))

                volume_id = ec2_volume.volume_id
            else:
                # create Volume resource
                vol_resource_name = 'Volume' + device_letter.upper()
                vol_resource = _get_volume_resource(ec2, volume, output)
                resources[vol_resource_name] = vol_resource

                volume_id = {'Ref': vol_resource_name}

            # create VolumeAttachment resource
            vol_attachment_resource_name = 'VolumeAttachment' + device_letter.upper()
            device_name = '/dev/sd' + device_letter
            vol_attachment_resource = _get_volume_attachment_resource(volume_id, device_name)
            resources[vol_attachment_resource_name] = vol_attachment_resource

    return resources


def get_template_parameters(ec2, instance_config: InstanceConfig, instance_profile_arn: str, bucket_name: str,
                            key_pair_name: str, output: AbstractOutputWriter):
    # get AMI
    ami = get_ami(ec2, instance_config.ami_id, instance_config.ami_name)
    output.write('- AMI: "%s" (%s)' % (ami.name, ami.image_id))

    # check root volume size
    root_volume_size = instance_config.root_volume_size
    if root_volume_size and root_volume_size < ami.size:
        raise ValueError('Root volume size cannot be less than the size of AMI (%dGB).' % ami.size)
    elif not root_volume_size:
        # if a root volume size is not specified, make it 5GB larger than the AMI size
        root_volume_size = ami.size + 5

    # print info about the Docker data root
    ebs_volumes = [volume for volume in instance_config.volumes if isinstance(volume, EbsVolume)]
    if instance_config.docker_data_root:
        docker_data_volume_name = [volume.name for volume in ebs_volumes
                                   if is_subdir(instance_config.docker_data_root, volume.mount_dir)][0]
        output.write('- Docker data will be stored on the "%s" volume' % docker_data_volume_name)

    # create stack
    parameters = {
        'VpcId': get_vpc_id(ec2, instance_config.subnet_id),
        'InstanceProfileArn': instance_profile_arn,
        'InstanceType': instance_config.instance_type,
        'KeyName': key_pair_name,
        'ImageId': ami.image_id,
        'RootVolumeSize': str(root_volume_size),
        'DockerDataRootDirectory': instance_config.docker_data_root,
        'InstanceNameTag': instance_config.ec2_instance_name,
        'HostProjectDirectory': instance_config.host_project_dir,
        'LogsS3Path': get_logs_s3_path(bucket_name, instance_config.name),
    }

    return parameters
