import logging
import subprocess
from typing import List
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.deployment.container_commands.docker_commands import DockerCommands
from spotty.providers.aws.aws_resources.image import Image
from spotty.helpers.print_info import render_volumes_info_table
from spotty.providers.aws.aws_resources.volume import Volume
from spotty.providers.aws.deployment.abstract_aws_deployment import AbstractAwsDeployment
from spotty.providers.aws.deployment.checks import check_az_and_subnet, check_max_price
from spotty.providers.aws.config.ebs_volume import EbsVolume
from spotty.providers.aws.deployment.cf_templates.instance_template import prepare_instance_template, \
    get_template_parameters
from spotty.providers.aws.deployment.deletion_policies import apply_deletion_policies
from spotty.providers.aws.deployment.project_resources.instance_profile_stack import InstanceProfileStackResource
from spotty.providers.aws.errors.bucket_not_found import BucketNotFoundError
from spotty.providers.aws.helpers.logs import download_logs
from spotty.providers.aws.deployment.project_resources.bucket import BucketResource
from spotty.providers.aws.deployment.project_resources.instance_stack import InstanceStackResource
from spotty.providers.aws.helpers.s3_sync import check_aws_installed
from spotty.providers.aws.helpers.spotty_sync import get_local_to_s3_command


class InstanceDeployment(AbstractAwsDeployment):

    @property
    def bucket(self) -> BucketResource:
        return BucketResource(self._project_name, self.instance_config.region)

    @property
    def stack(self) -> InstanceStackResource:
        return InstanceStackResource(self._project_name, self.instance_config.name, self.instance_config.region)

    def get_instance(self):
        return self.stack.get_instance()

    def deploy(self, docker_commands: DockerCommands, output: AbstractOutputWriter, dry_run=False):
        project_config = self.instance_config.project_config

        # check availability zone and subnet configuration
        check_az_and_subnet(self._ec2, self.instance_config.region, self.instance_config.availability_zone,
                            self.instance_config.subnet_id)

        # get volumes
        volumes = self.instance_config.volumes

        # get deployment availability zone
        availability_zone = self._get_availability_zone(volumes)

        # check the maximum price for a spot instance
        check_max_price(self._ec2, self.instance_config.instance_type, self.instance_config.is_spot_instance,
                        self.instance_config.max_price, availability_zone)

        # create or get existing bucket for the project
        try:
            bucket_name = self.bucket.get_bucket()
        except BucketNotFoundError:
            if not dry_run:
                bucket_name = self.bucket.create_bucket()
                output.write('Bucket "%s" was created.' % bucket_name)
            else:
                bucket_name = None

        # sync the project with the S3 bucket
        if bucket_name is not None:
            self.upload_project_to_s3(bucket_name, output, dry_run=dry_run)

        # create or update instance profile
        if not dry_run:
            instance_profile_stack = InstanceProfileStackResource(
                self._project_name, self.instance_config.name, self.instance_config.region)
            if not self.instance_config.instance_profile_arn:
                instance_profile_arn = instance_profile_stack.create_or_update_stack(
                    self.instance_config.managed_policy_arns, output=output)
            else:
                instance_profile_arn = self.instance_config.instance_profile_arn
        else:
            instance_profile_arn = None

        output.write('Preparing CloudFormation template...')

        # prepare CloudFormation template
        with output.prefix('  '):
            template = prepare_instance_template(
                ec2=self._ec2,
                instance_config=self.instance_config,
                docker_commands=docker_commands,
                volumes=volumes,
                availability_zone=availability_zone,
                bucket_name=bucket_name,
                output=output,
            )

            # get parameters for the template
            vpc_id = self.get_vpc_id()
            ami = self._get_ami()
            parameters = get_template_parameters(
                instance_config=self.instance_config,
                instance_profile_arn=instance_profile_arn,
                bucket_name=bucket_name,
                vpc_id=vpc_id,
                ami=ami,
                key_pair=self.key_pair,
                output=output,
                dry_run=dry_run,
            )

        # print information about the volumes
        output.write('\nVolumes:\n%s\n' % render_volumes_info_table(self.instance_config.volume_mounts, volumes))

        # create stack
        if not dry_run:
            stack = self.stack.create_or_update_stack(template, parameters, self.instance_config, output)

            if stack.status != 'CREATE_COMPLETE':
                logs_str = 'Please, see CloudFormation logs for the details.'

                # download CloudFormation logs from the instance if it's running
                if self.get_instance():
                    log_paths = download_logs(
                        bucket_name=bucket_name,
                        instance_name=self.instance_config.name,
                        stack_uuid=stack.stack_uuid,
                        region=self.instance_config.region,
                    )

                    logs_str = 'Please, see the logs for the details:\n  '
                    logs_str += '\n  '.join(log_paths)

                raise ValueError('Stack "%s" was not created.\n%s' % (stack.name, logs_str))

    def delete(self, output: AbstractOutputWriter):
        # terminate the instance
        instance = self.get_instance()
        if instance:
            output.write('Terminating the instance... ', newline=False)
            instance.terminate()
            instance.wait_instance_terminated()
            output.write('DONE')
        else:
            output.write('The instance was already terminated.')

        # delete the stack in background if it exists
        self.stack.delete_stack(output, no_wait=True)

        output.write('Applying deletion policies for the volumes...')

        # apply deletion policies for the volumes
        with output.prefix('  '):
            apply_deletion_policies(self._ec2, self.instance_config.volumes, output)

    def upload_project_to_s3(self, bucket_name: str, output: AbstractOutputWriter, dry_run=False):
        # check AWS CLI is installed
        check_aws_installed()

        # sync the project with the S3 bucket
        output.write('Syncing the project with S3 bucket...')
        local_cmd = get_local_to_s3_command(
            local_project_dir=self.instance_config.project_config.project_dir,
            bucket_name=bucket_name,
            region=self.instance_config.region,
            sync_filters=self.instance_config.project_config.sync_filters,
            dry_run=dry_run,
        )
        logging.debug('Local sync command: ' + local_cmd)

        # execute the command locally
        exit_code = subprocess.call(local_cmd, shell=True)
        if exit_code != 0:
            raise ValueError('Failed to upload the project files to the S3 bucket.')

    def _get_availability_zone(self, volumes: List[AbstractInstanceVolume]):
        """Checks that existing volumes located in the same AZ and the AZ from the
        config file matches volumes AZ.

        Args:
            volumes: List of volume objects.

        Returns:
            The final AZ where the instance should be run or an empty string if
            the instance can be run in any AZ.

        Raises:
            ValueError: AZ in the config file doesn't match the AZs of the volumes or
                AZs of the volumes are different.
        """
        availability_zone = self.instance_config.availability_zone
        for volume in volumes:
            if isinstance(volume, EbsVolume):
                ec2_volume = Volume.get_by_name(self._ec2, volume.ec2_volume_name)
                if ec2_volume:
                    if availability_zone and (availability_zone != ec2_volume.availability_zone):
                        raise ValueError(
                            'The availability zone in the configuration file doesn\'t match the availability zone '
                            'of the existing volume or you have two existing volumes in different availability '
                            'zones.')

                    # update availability zone
                    availability_zone = ec2_volume.availability_zone

        return availability_zone

    def _get_ami(self) -> Image:
        """Returns an AMI that should be used for deployment.

        Raises:
            ValueError: If an AMI not found.
        """
        if self.instance_config.ami_id:
            # get an AMI by ID if the "amiId" parameter is specified
            image = Image.get_by_id(self._ec2, self.instance_config.ami_id)
            if not image:
                raise ValueError('AMI with ID=%s not found.' % self.instance_config.ami_id)
        else:
            # try to get an AMI by its name (if the "amiName" parameter is not specified, the default value is used)
            image = Image.get_by_name(self._ec2, self.instance_config.ami_name)
            if not image:
                if self.instance_config.has_ami_name:
                    # if an AMI name was explicitly specified in the config, but the AMI was not found, raise an error
                    raise ValueError('AMI with the name "%s" was not found.' % self.instance_config.ami_name)
                else:
                    # get the latest "Deep Learning Base AMI"
                    res = self._ec2.describe_images(
                        Owners=['amazon'],
                        Filters=[{'Name': 'name', 'Values': ['Deep Learning AMI (Ubuntu 16.04) Version*']}],
                    )

                    if not len(res['Images']):
                        raise ValueError('AWS Deep Learning AMI not found.\n'
                                         'Use the "spotty aws create-ami" command to create an AMI with NVIDIA Docker.')

                    image_info = sorted(res['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]
                    image = Image(self._ec2, image_info)

        return image
