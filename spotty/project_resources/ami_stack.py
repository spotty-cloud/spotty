import yaml
from cfn_tools import CfnYamlLoader, CfnYamlDumper
from spotty.utils import data_dir, random_string


class AmiStackResource(object):

    def __init__(self, cf):
        self._cf = cf

    def prepare_template(self, availability_zone: str, subnet_id: str, on_demand: bool, key_name: str):
        """Prepares CloudFormation template to run a Spot Instance."""

        # read and update CF template
        with open(data_dir('create_ami.yaml')) as f:
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
            template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['NetworkInterfaces'] = [{
                'SubnetId': subnet_id,
                'DeviceIndex': 0,
            }]

        # run on-demand instance
        if on_demand:
            del template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['InstanceMarketOptions']

        return yaml.dump(template, Dumper=CfnYamlDumper)

    def create_stack(self, template: str, instance_type: str, ami_name: str, key_name: str):
        """Runs CloudFormation template."""
        params = {
            'InstanceType': instance_type,
            'ImageName': ami_name,
        }

        if key_name:
            params['KeyName'] = key_name

        stack_name = 'spotty-nvidia-docker-ami-%s' % random_string(8)
        res = self._cf.create_stack(
            StackName=stack_name,
            TemplateBody=template,
            Parameters=[{'ParameterKey': key, 'ParameterValue': value} for key, value in params.items()],
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        return res, stack_name
