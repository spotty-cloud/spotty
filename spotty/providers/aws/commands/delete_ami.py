from argparse import ArgumentParser, Namespace
import boto3
from spotty.commands.abstract_command import AbstractCommand
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.aws_resources.image import Image
from spotty.providers.aws.aws_resources.stack import Stack
from spotty.providers.aws.config.validation import DEFAULT_AMI_NAME


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
        ami = Image.get_by_name(ec2, ami_name)
        if not ami:
            raise ValueError('AMI with name "%s" not found.' % ami_name)

        # get stack ID for the image
        stack_id = ami.get_tag_value('spotty:stack-id')
        if not stack_id:
            raise ValueError('AMI wasn\'t created by Spotty')

        # ask user to confirm the deletion
        confirm = input('AMI "%s" (ID=%s) will be deleted.\n'
                        'Type "y" to confirm: '
                        % (ami_name, ami.image_id))
        if confirm != 'y':
            output.write('You didn\'t confirm the operation.')
            return

        # delete the image
        stack = Stack.get_by_name(cf, stack_id)
        stack.delete()

        output.write('Waiting for the AMI to be deleted...')

        # wait for the deletion to be completed
        with output.prefix('  '):
            stack = stack.wait_status_changed(waiting_status='DELETE_IN_PROGRESS',
                                              resource_messages=[],
                                              resource_success_status='DELETE_COMPLETE', output=output)

        if stack.status == 'DELETE_COMPLETE':
            output.write('\n'
                         '-----------------------------\n'
                         'AMI was successfully deleted.\n'
                         '-----------------------------')
        else:
            raise ValueError('Stack "%s" not deleted.\n'
                             'See CloudFormation and CloudWatch logs for details.' % stack_id)
