import boto3
from argparse import Namespace, ArgumentParser
from spotty.commands.abstract_command import AbstractCommand
from spotty.providers.aws.helpers.resources import is_gpu_instance, wait_stack_status_changed, check_az_and_subnet, \
    get_ami
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.validation import DEFAULT_AMI_NAME
from spotty.providers.aws.project_resources.ami_stack import AmiStackResource


class CreateAmiCommand(AbstractCommand):

    name = 'create-ami'
    description = 'Create AMI with NVIDIA Docker'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-r', '--region', type=str, required=True, help='AWS region')
        parser.add_argument('-i', '--instance-type', type=str, default='p2.xlarge', help='GPU instance type')
        parser.add_argument('-n', '--ami-name', type=str, default=DEFAULT_AMI_NAME, help='AMI name')
        parser.add_argument('-z', '--availability-zone', type=str, default=None, help='Run instance in particular '
                                                                                      'availability zone')
        parser.add_argument('-s', '--subnet-id', type=str, default=None, help='Use specific subnet to run an instance')
        parser.add_argument('-k', '--key-name', type=str, default=None, help='EC2 Key Pair name')
        parser.add_argument('--on-demand', action='store_true', help='Run On-Demand instance instead of a Spot '
                                                                     'instance')

    def run(self, args: Namespace, output: AbstractOutputWriter):
        region = args.region
        instance_type = args.instance_type
        ami_name = args.ami_name
        availability_zone = args.availability_zone
        subnet_id = args.subnet_id
        key_name = args.key_name
        on_demand = args.on_demand

        # check that it's a GPU instance type
        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # check that an image with this name doesn't exist yet
        ami_info = get_ami(ec2, ami_name)
        if ami_info:
            raise ValueError('AMI with name "%s" already exists.' % ami_name)

        # check availability zone and subnet
        check_az_and_subnet(ec2, availability_zone, subnet_id, region)

        # prepare CF template
        ami_stack = AmiStackResource(cf)
        template = ami_stack.prepare_template(availability_zone, subnet_id, key_name, on_demand)

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
        with output.prefix('  '):
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
