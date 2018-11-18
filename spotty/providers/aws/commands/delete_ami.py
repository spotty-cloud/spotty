from argparse import ArgumentParser, Namespace
import boto3
from spotty.commands.abstract_command import AbstractCommand
from spotty.providers.aws.helpers.resources import wait_stack_status_changed, get_ami
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.validation import DEFAULT_AMI_NAME


class DeleteAmiCommand(AbstractCommand):

    name = 'delete-ami'
    description = 'Delete AMI with NVIDIA Docker'

    def configure(self, parser: ArgumentParser):
        super().configure(parser)
        parser.add_argument('-r', '--region', type=str, required=True, help='AWS region')
        parser.add_argument('-n', '--ami-name', type=str, default=DEFAULT_AMI_NAME, help='AMI name')

    def run(self, args: Namespace, output: AbstractOutputWriter):
        region = args.region
        ami_name = args.ami_name

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # get image info
        ami_info = get_ami(ec2, ami_name)
        if not ami_info:
            raise ValueError('AMI with name "%s" not found.' % ami_name)

        # get stack ID for the image
        tag_values = [tag['Value'] for tag in ami_info['Tags'] if tag['Key'] == 'spotty:stack-id']
        if not len(tag_values):
            raise ValueError('AMI wasn\'t created by Spotty')

        # ask user to confirm the deletion
        ami_id = ami_info['ImageId']
        confirm = input('AMI "%s" (ID=%s) will be deleted.\n'
                        'Type "y" to confirm: '
                        % (ami_name, ami_id))
        if confirm != 'y':
            output.write('You didn\'t confirm the operation.')
            return

        # delete the image
        stack_id = tag_values[0]
        cf.delete_stack(StackName=stack_id)

        output.write('Waiting for the AMI to be deleted...')

        # wait for the deletion to be completed
        status, stack = wait_stack_status_changed(cf, stack_id=stack_id, waiting_status='DELETE_IN_PROGRESS',
                                                  resource_messages=[],
                                                  resource_success_status='DELETE_COMPLETE', output=output)

        if status == 'DELETE_COMPLETE':
            output.write('\n'
                         '--------------------\n'
                         'AMI was successfully deleted.\n'
                         '--------------------')
        else:
            raise ValueError('Stack "%s" not deleted.\n'
                             'See CloudFormation and CloudWatch logs for details.' % stack_id)
