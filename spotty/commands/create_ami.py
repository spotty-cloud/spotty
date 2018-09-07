import yaml
import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import is_gpu_instance, wait_stack_status_changed
from spotty.helpers.validation import validate_ami_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.utils import data_dir, random_string
from cfn_tools import CfnYamlLoader, CfnYamlDumper


class CreateAmiCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'create-ami'

    @staticmethod
    def get_description():
        return 'Create AMI with NVIDIA Docker'

    @staticmethod
    def _validate_config(config):
        return validate_ami_config(config)

    def run(self, output: AbstractOutputWriter):
        # check that it's a GPU instance type
        instance_type = self._config['instance']['instanceType']
        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        region = self._config['instance']['region']
        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # check that an image with this name doesn't exist yet
        ami_name = self._config['instance']['amiName']
        res = ec2.describe_images(Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])

        if len(res['Images']):
            raise ValueError('AMI with name "%s" already exists.' % ami_name)

        # read and update CF template
        with open(data_dir('create_ami.yaml')) as f:
            template = yaml.load(f, Loader=CfnYamlLoader)

        # remove key parameter if key is not provided
        key_name = self._config['instance'].get('keyName', '')
        if not key_name:
            del template['Parameters']['KeyName']
            del template['Resources']['SpotInstanceLaunchTemplate']['Properties']['LaunchTemplateData']['KeyName']

        # create stack
        params = [
            {'ParameterKey': 'InstanceType', 'ParameterValue': instance_type},
            {'ParameterKey': 'ImageName', 'ParameterValue': ami_name},
        ]
        if key_name:
            params.append({'ParameterKey': 'KeyName', 'ParameterValue': key_name})

        stack_name = 'spotty-nvidia-docker-ami-%s' % random_string(8)
        res = cf.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template, Dumper=CfnYamlDumper),
            Parameters=params,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        output.write('Waiting for the AMI to be created...')

        resource_messages = [
            ('InstanceProfile', 'creating IAM role for the instance'),
            ('SpotInstance', 'launching the instance'),
            ('InstanceReadyWaitCondition', 'installing NVIDIA Docker'),
            ('AMICreatedWaitCondition', 'creating AMI and terminating the instance'),
        ]

        # wait for the stack to be created
        status, stack = wait_stack_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                                  resource_messages=resource_messages,
                                                  resource_success_status='CREATE_COMPLETE', output=output)

        if status == 'CREATE_COMPLETE':
            ami_id = [row['OutputValue'] for row in stack['Outputs'] if row['OutputKey'] == 'NewAMI'][0]

            output.write('\n'
                         '--------------------\n'
                         'AMI "%s" (ID=%s) was successfully created.\n'
                         'Use "spotty start" command to run a Spot Instance.\n'
                         '--------------------' % (ami_name, ami_id))
        else:
            raise ValueError('Stack "%s" was not created.\n'
                             'See CloudFormation and CloudWatch logs for details.' % stack_name)
