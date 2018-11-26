import boto3
from botocore.exceptions import ClientError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.resources.stack import Stack
from spotty.providers.aws.utils import data_dir


def create_or_update_instance_profile(region, output: AbstractOutputWriter, dry_run=False):
    """Creates or updates instance profile.
    It was moved to a separate stack because creating of an instance profile resource takes 2 minutes.
    """
    if dry_run:
        output.write('Updating IAM role for the instance...')
        return ''

    cf = boto3.client('cloudformation', region_name=region)

    instance_profile_stack_name = 'spotty-instance-profile'
    with open(data_dir('create_instance_profile.yaml')) as f:
        instance_profile_stack_template = f.read()

    stack = Stack.get_by_name(cf, instance_profile_stack_name)
    if stack:
        output.write('Updating IAM role for the instance...')

        try:
            updated_stack = stack.update_stack(
                cf=cf,
                StackName=instance_profile_stack_name,
                TemplateBody=instance_profile_stack_template,
                Capabilities=['CAPABILITY_IAM'],
            )
        except ClientError as e:
            # the stack was not updated because there is no changes
            updated_stack = None
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code != 'ValidationError':
                raise e

        if updated_stack:
            # wait for the stack to be updated
            stack = updated_stack.wait_status_changed(waiting_status='UPDATE_IN_PROGRESS',
                                                      resource_messages=None, resource_success_status=None,
                                                      output=output)
    else:
        output.write('Creating IAM role for the instance...')

        stack = Stack.create_stack(
            cf=cf,
            StackName=instance_profile_stack_name,
            TemplateBody=instance_profile_stack_template,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        # wait for the stack to be created
        stack = stack.wait_status_changed(waiting_status='CREATE_IN_PROGRESS',
                                          resource_messages=None, resource_success_status=None,
                                          output=output)

    if stack.status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
        raise ValueError('Stack "%s" failed.\n'
                         'Please, see CloudFormation logs for the details.' % instance_profile_stack_name)

    profile_arn = [row['OutputValue'] for row in stack.outputs if row['OutputKey'] == 'ProfileArn'][0]

    return profile_arn
