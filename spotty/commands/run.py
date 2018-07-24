from argparse import ArgumentParser
import yaml
import boto3
from botocore.exceptions import WaiterError
from spotty.commands.abstract_config import AbstractConfigCommand
from spotty.commands.utils.stack import wait_for_status_changed, stack_exists
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.utils import data_dir, random_string
from cfn_tools import CfnYamlLoader, CfnYamlDumper


class RunCommand(AbstractConfigCommand):

    @staticmethod
    def get_name() -> str:
        return 'run'

    @staticmethod
    def configure(parser: ArgumentParser):
        AbstractConfigCommand.configure(parser)
        parser.add_argument('script-name', metavar='SCRIPT_NAME', type=str, default='', nargs='?', help='Script name')

    def run(self, output: AbstractOutputWriter):
        # TODO: check config
        config = self._config['instance']

        stack_name = config['stackName']
        region = config['region']
        instance_type = config['instanceType']
        key_name = config['keyName']
        ami_name = config['amiName']
        volume = config['volumes'][0]

        # if not instance_type:
        #     raise ValueError('Instance type not specified')

        cf = boto3.client('cloudformation', region_name=region)
        ec2 = boto3.client('ec2', region_name=region)

        # check that the stack doesn't exist
        if stack_exists(cf, stack_name):
            raise ValueError('Stack "%s" already exists. Use "spotty stop" command to delete the stack.'
                             % stack_name)

        # get image info
        res = ec2.describe_images(Filters=[
            {'Name': 'name', 'Values': [ami_name]},
        ])

        # check that only one image with such name exists
        if not len(res['Images']):
            output.write('Image with Name=%s not found.' % ami_name)
            output.write('Use "spotty create-ami" command to create a Docker AMI.')
            return
        elif len(res['Images']) > 1:
            raise ValueError('Several images with Name=%s found.' % ami_name)

        ami_id = res['Images'][0]['ImageId']

        # read and update CF template
        with open(data_dir('run_container.yaml')) as f:
            template = yaml.load(f, Loader=CfnYamlLoader)

        # remove KeyName parameter if key is not provided
        if not key_name:
            del template['Parameters']['KeyName']
            del template['Resources']['SpotFleet']['Properties']['SpotFleetRequestConfigData']['LaunchSpecifications'][0]['KeyName']

        # get snapshot by its name
        snapshot_name = volume['snapshotName']
        res = ec2.describe_snapshots(Filters=[
            {'Name': 'tag:Name', 'Values': [snapshot_name]},
        ])

        if not len(res['Snapshots']):
            if 'size' not in volume:
                raise ValueError('Size of new volume is required (snapshot "%s" not found).' % snapshot_name)
        elif len(res['Snapshots']) > 1:
            raise ValueError('Several snapshots with Name=%s found.' % ami_name)
        else:
            # set snapshot ID
            snapshot = res['Snapshots'][0]
            template['Resources']['Volume1']['Properties']['SnapshotId'] = snapshot['SnapshotId']

            # delete original snapshot if new snapshot will be created
            if not volume.get('deleteOnTermination', False):
                template['Resources']['DeleteSnapshot']['Properties']['SnapshotId'] = snapshot['SnapshotId']

            # check size of the volume
            if 'size' in volume:
                if volume['size'] < snapshot['VolumeSize']:
                    raise ValueError('Requested size of the volume (%dGB) is less than size of the snapshot (%dGB).'
                                     % (volume['size'], snapshot['VolumeSize']))
                elif volume['size'] > snapshot['VolumeSize']:
                    output.write('Size of the snapshot will be increased from %dGB to %dGB.'
                                 % (snapshot['VolumeSize'], volume['size']))

        # set size of the volume
        if 'size' in volume:
            template['Resources']['Volume1']['Properties']['Size'] = volume['size']

        # update deletion policy
        if volume.get('deleteOnTermination', False):
            template['Resources']['Volume1']['DeletionPolicy'] = 'Delete'

        # set tag
        template['Resources']['Volume1']['Properties']['Tags'] = [{'Key': 'Name', 'Value': snapshot_name}]

        # create stack
        params = [
            {'ParameterKey': 'InstanceType', 'ParameterValue': instance_type},
            {'ParameterKey': 'ImageId', 'ParameterValue': ami_id},
            {'ParameterKey': 'VolumeMountDirectory', 'ParameterValue': volume.get('directory', '')},
            {'ParameterKey': 'DockerDataRootDirectory', 'ParameterValue': config['docker'].get('dataRoot', '')},
        ]
        if key_name:
            params.append({'ParameterKey': 'KeyName', 'ParameterValue': key_name})

        res = cf.create_stack(
            StackName=stack_name,
            TemplateBody=yaml.dump(template, Dumper=CfnYamlDumper),
            Parameters=params,
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
        )

        output.write('Waiting for the stack to be created...')

        # wait for the stack to be created
        status, stack = wait_for_status_changed(cf, stack_id=res['StackId'], waiting_status='CREATE_IN_PROGRESS',
                                                output=output)

        if status == 'CREATE_COMPLETE':
            ip_address = [row['OutputValue'] for row in stack['Outputs'] if row['OutputKey'] == 'InstanceIpAddress'][0]
            output.write('Stack "%s" was successfully created.' % stack_name)
            output.write('IP address of the instance: %s' % ip_address)
        else:
            raise ValueError('Stack "%s" not created. See CloudFormation and CloudWatch logs for details.' % stack_name)
