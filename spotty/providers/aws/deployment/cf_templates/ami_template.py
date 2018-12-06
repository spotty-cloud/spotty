import os
import yaml
from cfn_tools import CfnYamlDumper, CfnYamlLoader


def prepare_ami_template(availability_zone: str, subnet_id: str, key_name: str, on_demand=False):
    """Prepares CloudFormation template to run a Spot Instance."""

    # read and update CF template
    with open(os.path.join(os.path.dirname(__file__), 'data', 'create_ami.yaml')) as f:
        template = yaml.load(f, Loader=CfnYamlLoader)

    # remove key parameter if key is not provided
    if not key_name:
        del template['Parameters']['KeyName']
        del template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['KeyName']

    # set availability zone
    if availability_zone:
        template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['Placement'] = {
            'AvailabilityZone': availability_zone,
        }

    # set subnet
    if subnet_id:
        template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['NetworkInterfaces'] = [
            {
                'SubnetId': subnet_id,
                'DeviceIndex': 0,
            }]

    # run on-demand instance
    if on_demand:
        del template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData'][
            'InstanceMarketOptions']

    return yaml.dump(template, Dumper=CfnYamlDumper)
