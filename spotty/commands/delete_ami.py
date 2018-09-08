import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.helpers.resources import wait_stack_status_changed
from spotty.helpers.validation import validate_ami_config
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class DeleteAmiCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'delete-ami'

    @staticmethod
    def get_description():
        return 'Delete AMI with NVIDIA Docker'

    @staticmethod
    def _validate_config(config):
        return validate_ami_config(config)

    def run(self, output: AbstractOutputWriter):
        region = self._config['instance']['region']
        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # get image info
        ami_name = self._config['instance']['amiName']
        res = ec2.describe_images(Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])

        # check that only one image with such name exists
        if not len(res['Images']):
            raise ValueError('AMI with name "%s" not found.' % ami_name)
        elif len(res['Images']) > 1:
            raise ValueError('Several images with Name=%s found.' % ami_name)

        # get stack ID for the image
        tag_values = [tag['Value'] for tag in res['Images'][0]['Tags'] if tag['Key'] == 'spotty:stack-id']
        if not len(tag_values):
            raise ValueError('AMI wasn\'t created by Spotty')

        # ask user to confirm the deletion
        ami_id = res['Images'][0]['ImageId']
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
