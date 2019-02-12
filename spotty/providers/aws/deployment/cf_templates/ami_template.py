import os
import yaml
from cfn_tools import CfnYamlDumper, CfnYamlLoader


def prepare_ami_template(availability_zone: str, subnet_id: str, debug_mode: bool = False, on_demand: bool = False):
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
            }]

    # run on-demand instance
    if on_demand:
        del template['Resources']['InstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
            'InstanceMarketOptions']

    return yaml.dump(template, Dumper=CfnYamlDumper)
