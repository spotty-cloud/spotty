from botocore.exceptions import ClientError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.helpers.resources import stack_exists, wait_stack_status_changed
from spotty.utils import data_dir


def create_or_update_instance_profile(cf, output: AbstractOutputWriter):
    """Creates or updates instance profile.
    It was moved to a separate stack because creating of an instance profile resource takes 2 minutes.
    """
    instance_profile_stack_name = 'spotty-instance-profile'
    with open(data_dir('create_instance_profile.yaml')) as f:
        instance_profile_stack_template = f.read()

    if stack_exists(cf, instance_profile_stack_name):
        try:
            res = cf.update_stack(
                StackName=instance_profile_stack_name,
                TemplateBody=instance_profile_stack_template,
                Capabilities=['CAPABILITY_IAM'],
            )
        except ClientError as e:
            res = {}
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code != 'ValidationError':
                raise e

        if res:
            output.write('Updating IAM role for the instance...')

            # wait for the stack to be updated
            status, info = wait_stack_status_changed(cf, stack_id=res['StackId'], waiting_status='UPDATE_IN_PROGRESS',
                                                     resource_messages=None, resource_success_status=None,
                                                     output=output)
        else:
            info = cf.describe_stacks(StackName=instance_profile_stack_name)['Stacks'][0]
            status = info['StackStatus']
    else:
        output.write('Creating IAM role for the instance...')

        res = cf.create_stack(
            StackName=instance_profile_stack_name,
            TemplateBody=instance_profile_stack_template,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        # wait for the stack to be created
        status, info = wait_stack_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                                 resource_messages=None, resource_success_status=None,
                                                 output=output)

    if status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
        raise ValueError('Stack "%s" failed.\n'
                         'Please, see CloudFormation logs for the details.' % instance_profile_stack_name)

    profile_arn = [row['OutputValue'] for row in info['Outputs'] if row['OutputKey'] == 'ProfileArn'][0]

    return profile_arn
