import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import is_gpu_instance, wait_stack_status_changed, get_ami, check_az_and_subnet
from spotty.helpers.validation import validate_ami_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.project_resources.ami_stack import AmiStackResource


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
        instance_config = self._config['instance']

        # check that it's a GPU instance type
        instance_type = instance_config['instanceType']
        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        region = instance_config['region']
        availability_zone = instance_config['availabilityZone']
        subnet_id = instance_config['subnetId']

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # check that an image with this name doesn't exist yet
        ami_name = instance_config['amiName']
        ami_info = get_ami(ec2, ami_name)
        if ami_info:
            raise ValueError('AMI with name "%s" already exists.' % ami_name)

        # check availability zone and subnet
        check_az_and_subnet(ec2, availability_zone, subnet_id, region)

        ami_stack = AmiStackResource(cf)

        # prepare CF template
        on_demand = instance_config['onDemandInstance']
        key_name = instance_config.get('keyName', '')
        template = ami_stack.prepare_template(availability_zone, subnet_id, on_demand, key_name)

        # create stack
        res, stack_name = ami_stack.create_stack(template, instance_type, ami_name, key_name)

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
