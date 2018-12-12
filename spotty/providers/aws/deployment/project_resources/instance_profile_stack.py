import boto3
from botocore.exceptions import ClientError, WaiterError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.aws_resources.stack import Stack
from spotty.providers.aws.deployment.cf_templates.instance_profile_template import prepare_instance_profile_template


def create_or_update_instance_profile(region, output: AbstractOutputWriter):
    """Creates or updates an instance profile.
    It was moved to a separate stack because creating of an instance profile resource takes 2 minutes.
    """
    cf = boto3.client('cloudformation', region_name=region)

    instance_profile_stack_name = 'spotty-instance-profile'
    template = prepare_instance_profile_template()

    stack = Stack.get_by_name(cf, instance_profile_stack_name)
    try:
        if stack:
            _update_stack(cf, stack, template, output)
        else:
            _create_stack(cf, instance_profile_stack_name, template, output)

        stack = Stack.get_by_name(cf, instance_profile_stack_name)
    except WaiterError:
        stack = None

    if not stack or stack.status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
        raise ValueError('Stack "%s" was not created.\n'
                         'Please, see CloudFormation logs for the details.' % instance_profile_stack_name)

    profile_arn = [row['OutputValue'] for row in stack.outputs if row['OutputKey'] == 'ProfileArn'][0]

    return profile_arn


def _create_stack(cf, stack_name, template: str, output: AbstractOutputWriter):
    output.write('Creating IAM role for the instance...')

    stack = Stack.create_stack(
        cf=cf,
        StackName=stack_name,
        TemplateBody=template,
        Capabilities=['CAPABILITY_IAM'],
        OnFailure='DELETE',
    )

    # wait for the stack to be created
    stack.wait_stack_created(delay=15)


def _update_stack(cf, stack: Stack, template: str, output: AbstractOutputWriter):
    try:
        updated_stack = stack.update_stack(
            cf=cf,
            StackName=stack.name,
            TemplateBody=template,
            Capabilities=['CAPABILITY_IAM'],
        )
    except ClientError as e:
        # the stack was not updated because there are no changes
        updated_stack = None
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code != 'ValidationError':
            raise e

    if updated_stack:
        # wait for the stack to be updated
        output.write('Updating IAM role for the instance...')
        updated_stack.wait_stack_updated(delay=15)
