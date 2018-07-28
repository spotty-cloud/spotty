import yaml
import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.helpers.resources import is_gpu_instance, wait_for_status_changed
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.utils import data_dir, random_string
from cfn_tools import CfnYamlLoader, CfnYamlDumper


class CreateAmiCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'create-ami'

    def run(self, output: AbstractOutputWriter):
        # TODO: check config
        region = self._config['instance']['region']
        instance_type = self._config['instance']['instanceType']
        key_name = self._config['instance'].get('keyName', '')

        # TODO: Constraints: 3-128 alphanumeric characters, parentheses (()), square brackets ([]), spaces ( ), periods (.), slashes (/), dashes (-), single quotes ('), at-signs (@), or underscores(_)
        ami_name = self._config['instance']['amiName']

        if not instance_type:
            raise ValueError('Instance type not specified')

        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # check that an image with this name doesn't exist yet
        res = ec2.describe_images(Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])

        if len(res['Images']):
            raise ValueError('Image with Name=%s already exists.' % ami_name)

        # read and update CF template
        with open(data_dir('create_ami.yaml')) as f:
            template = yaml.load(f, Loader=CfnYamlLoader)

        if not key_name:
            del template['Parameters']['KeyName']
            del template['Resources']['SpotFleet']['Properties']['SpotFleetRequestConfigData']['LaunchSpecifications'][0]['KeyName']

        # create stack
        params = [
            {'ParameterKey': 'InstanceType', 'ParameterValue': instance_type},
            {'ParameterKey': 'ImageName', 'ParameterValue': ami_name},
        ]
        if key_name:
            params.append({'ParameterKey': 'KeyName', 'ParameterValue': key_name})

        stack_name = 'spotty-ami-' + random_string(8)
        res = cf.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template, Dumper=CfnYamlDumper),
            Parameters=params,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        output.write('Waiting for the AMI to be created...')

        # wait for the stack to be created
        status, stack = wait_for_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                                output=output)

        if status == 'CREATE_COMPLETE':
            ami_id = [row['OutputValue'] for row in stack['Outputs'] if row['OutputKey'] == 'NewAMI'][0]
            output.write('AMI "%s" (ID=%s) was successfully created.' % (ami_name, ami_id))
        else:
            raise ValueError('Stack "%s" not created. See CloudFormation and CloudWatch logs for details.' % stack_name)
