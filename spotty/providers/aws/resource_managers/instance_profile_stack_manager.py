import boto3
from botocore.exceptions import ClientError, WaiterError
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.cfn_templates.instance_profile.template import prepare_instance_profile_template
from spotty.providers.aws.resources.stack import Stack


class InstanceProfileStackManager(object):

    def __init__(self, project_name: str, instance_name: str, region: str):
        self._cf = boto3.client('cloudformation', region_name=region)
        self._region = region
        self._stack_name = 'spotty-instance-profile-%s-%s' % (project_name.lower(), instance_name.lower())

    def create_or_update_stack(self, managed_policy_arns: list, output: AbstractOutputWriter):
        """Creates or updates an instance profile.
        It was moved to a separate stack because creating of an instance profile resource takes 2 minutes.
        """
        # check that policies exist
        iam = boto3.client('iam', region_name=self._region)
        for policy_arn in managed_policy_arns:
            # if the policy doesn't exist, an error will be raised
            iam.get_policy(PolicyArn=policy_arn)

        template = prepare_instance_profile_template(managed_policy_arns)

        stack = Stack.get_by_name(self._cf, self._stack_name)
        try:
            if stack:
                # update the stack and wait until it will be updated
                self._update_stack(template, output)
            else:
                # create the stack and wait until it will be created
                self._create_stack(template, output)

            stack = Stack.get_by_name(self._cf, self._stack_name)
        except WaiterError:
            stack = None

        if not stack or stack.status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            raise ValueError('Stack "%s" was not created.\n'
                             'Please, see CloudFormation logs for the details.' % self._stack_name)

        profile_arn = [row['OutputValue'] for row in stack.outputs if row['OutputKey'] == 'ProfileArn'][0]

        return profile_arn

    def _create_stack(self, template: str, output: AbstractOutputWriter):
        """Creates the stack and waits until it will be created."""
        output.write('Creating IAM role for the instance...')

        stack = Stack.create_stack(
            cf=self._cf,
            StackName=self._stack_name,
            TemplateBody=template,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        # wait for the stack to be created
        stack.wait_stack_created(delay=15)

    def _update_stack(self, template: str, output: AbstractOutputWriter):
        """Updates the stack and waits until it will be updated."""
        try:
            updated_stack = Stack.update_stack(
                cf=self._cf,
                StackName=self._stack_name,
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
