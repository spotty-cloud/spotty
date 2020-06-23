import os
import yaml
from cfn_tools import CfnYamlDumper, CfnYamlLoader
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deployment.project_resources.key_pair import KeyPairResource


def prepare_ami_template(availability_zone: str, subnet_id: str, debug_mode: bool = False,
                         is_spot_instance: bool = False):
    """Prepares CloudFormation template to run a Spot Instance."""

    # read and update CF template
    with open(os.path.join(os.path.dirname(__file__), 'data', 'ami.yaml')) as f:
        template = yaml.load(f, Loader=CfnYamlLoader)

    # remove the key parameter if it's not a debug mode
    if not debug_mode:
        del template['Parameters']['KeyName']
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['KeyName']

    # set availability zone
    if availability_zone:
        template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['Placement'] = {
            'AvailabilityZone': availability_zone,
        }

    # set subnet
    if subnet_id:
        template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['NetworkInterfaces'] = [
            {
                'SubnetId': subnet_id,
                'DeviceIndex': 0,
                'Groups': template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
                    'SecurityGroupIds'],
            }]
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData']['SecurityGroupIds']

    # run on-demand instance
    if not is_spot_instance:
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
            'InstanceMarketOptions']

    return yaml.dump(template, Dumper=CfnYamlDumper)


def get_template_parameters(instance_config: InstanceConfig, image_version: str, vpc_id: str,
                            key_pair: KeyPairResource, debug_mode: bool = False):
    parameters = {
        'ImageVersion': image_version,
        'VpcId': vpc_id,
        'InstanceType': instance_config.instance_type,
        'ImageName': instance_config.ami_name,
        'InstanceNameTag': 'spotty-ami-%s' % instance_config.ami_name.lower(),
        'NvidiaDriverVersion': '410',
        'DockerCEVersion': '19.03.5',
        'ContainerdIOVersion': '1.2.10-3',
        'NvidiaContainerToolkitVersion': '1.0.5-1',
    }

    if debug_mode:
        parameters['DebugMode'] = 'true'
        parameters['KeyName'] = key_pair.get_or_create_key()  # get or create a key pair

    return parameters
