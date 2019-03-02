import boto3
from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.aws.aws_resources.instance import Instance
from spotty.providers.aws.aws_resources.subnet import Subnet
from spotty.providers.aws.aws_resources.vpc import Vpc
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deployment.cf_templates.ami_template import prepare_ami_template
from spotty.providers.aws.deployment.checks import check_az_and_subnet, check_max_price
from spotty.providers.aws.deployment.project_resources.ami_stack import AmiStackResource
from spotty.providers.aws.aws_resources.image import Image
from spotty.providers.aws.config.validation import is_gpu_instance
from spotty.providers.aws.deployment.project_resources.key_pair import KeyPairResource


class AmiDeployment(object):

    def __init__(self, project_name: str, instance_config: InstanceConfig):
        self._project_name = project_name
        self._instance_config = instance_config
        self._ec2 = boto3.client('ec2', region_name=instance_config.region)

    @property
    def instance_config(self):
        return self._instance_config

    @property
    def ec2_instance_name(self) -> str:
        return '%s-%s-ami' % (self._project_name.lower(), self.instance_config.name.lower())

    @property
    def key_pair(self) -> KeyPairResource:
        return KeyPairResource(self._project_name, self.instance_config.region)

    @property
    def stack(self):
        return AmiStackResource(self.instance_config.ami_name, self.instance_config.region)

    def get_ami(self) -> Image:
        if self.instance_config.ami_id:
            raise ValueError('The "amiId" parameter cannot be used for creating or deleting an AMI.')

        return Image.get_by_name(self._ec2, self.instance_config.ami_name)

    def get_vpc_id(self) -> str:
        if self.instance_config.subnet_id:
            vpc_id = Subnet.get_by_id(self._ec2, self.instance_config.subnet_id).vpc_id
        else:
            default_vpc = Vpc.get_default_vpc(self._ec2)
            if not default_vpc:
                raise ValueError('Default VPC not found')

            vpc_id = default_vpc.vpc_id

        return vpc_id

    def deploy(self, debug_mode: bool, output: AbstractOutputWriter):
        # check that it's a GPU instance type
        instance_type = self.instance_config.instance_type
        if not is_gpu_instance(instance_type):
            raise ValueError('"%s" is not a GPU instance' % instance_type)

        # check that an image with this name doesn't exist yet
        ami = self.get_ami()
        if ami:
            raise ValueError('AMI with the name "%s" already exists.' % ami.name)

        # check availability zone and subnet
        check_az_and_subnet(self._ec2, self.instance_config.region, self.instance_config.availability_zone,
                            self.instance_config.subnet_id)

        # check the maximum price for a spot instance
        availability_zone = self.instance_config.availability_zone
        check_max_price(self._ec2, self.instance_config.instance_type, self.instance_config.on_demand,
                        self.instance_config.max_price, availability_zone)

        # prepare CF template
        subnet_id = self.instance_config.subnet_id
        on_demand = self.instance_config.on_demand
        template = prepare_ami_template(availability_zone, subnet_id, debug_mode, on_demand)

        # create stack
        parameters = self._get_template_parameters(debug_mode)
        self.stack.create_stack(template, parameters, debug_mode, output)

    def _get_template_parameters(self, debug_mode: bool = False):
        parameters = {
            'VpcId': self.get_vpc_id(),
            'InstanceType': self.instance_config.instance_type,
            'ImageName': self.instance_config.ami_name,
            'InstanceNameTag': self.ec2_instance_name,
        }

        if debug_mode:
            parameters['DebugMode'] = 'true'
            parameters['KeyName'] = self.key_pair.get_or_create_key()  # get or create a key pair

        return parameters

    def delete(self, output: AbstractOutputWriter):
        # get image info
        ami = self.get_ami()
        if not ami:
            raise ValueError('AMI with the name "%s" not found.' % self.instance_config.ami_name)

        # get stack ID for the image
        stack_id = ami.get_tag_value('spotty:stack-id')
        if not stack_id:
            raise ValueError('AMI "%s" wasn\'t created by Spotty.' % self.instance_config.ami_name)

        # ask user to confirm the deletion
        confirm = input('AMI "%s" (ID=%s) will be deleted.\n'
                        'Type "y" to confirm: ' % (ami.name, ami.image_id))
        if confirm != 'y':
            output.write('You didn\'t confirm the operation.')
            return

        self.stack.delete_stack(stack_id, output)

    def get_ip_address(self):
        instance = Instance.get_by_stack_name(self._ec2, self.stack.name)
        if not instance:
            return None

        if self._instance_config.local_ssh_port:
            return '127.0.0.1'

        return instance.public_ip_address
