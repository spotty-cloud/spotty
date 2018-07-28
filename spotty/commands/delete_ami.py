import boto3
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.helpers.resources import wait_for_status_changed
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter


class DeleteAmiCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'delete-ami'

    def run(self, output: AbstractOutputWriter):
        # TODO: check config
        region = self._config['instance']['region']
        ami_name = self._config['instance']['amiName']

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # get image info
        res = ec2.describe_images(Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])

        # check that only one image with such name exists
        if not len(res['Images']):
            raise ValueError('Image with Name=%s not found.' % ami_name)
        elif len(res['Images']) > 1:
            raise ValueError('Several images with Name=%s found.' % ami_name)

        # get stack ID for the image
        tag_values = [tag['Value'] for tag in res['Images'][0]['Tags'] if tag['Key'] == 'spotty:stack-id']
        if not len(tag_values):
            raise ValueError('AMI wasn\'t created by Spotty')

        # ask user to confirm the deletion
        ami_id = res['Images'][0]['ImageId']
        confirm = input('AMI "%s" (ID=%s) will be deleted. Type "y" to confirm: '
                        % (ami_name, ami_id))
        if confirm != 'y':
            output.write('You didn\'t confirm the operation.')
            return

        # delete the image
        stack_id = tag_values[0]
        cf.delete_stack(StackName=stack_id)

        output.write('Waiting for the AMI to be deleted...')

        # wait for the deletion to be completed
        status, stack = wait_for_status_changed(cf, stack_id=stack_id, waiting_status='DELETE_IN_PROGRESS',
                                                output=output)

        if status == 'DELETE_COMPLETE':
            output.write('AMI was successfully deleted.')
        else:
            raise ValueError('Stack "%s" not deleted. See CloudFormation and CloudWatch logs for details.' % stack_id)
