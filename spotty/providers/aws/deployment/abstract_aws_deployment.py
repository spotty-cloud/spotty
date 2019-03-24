from abc import ABC, abstractmethod
import boto3
from spotty.providers.aws.aws_resources.image import Image
from spotty.providers.aws.aws_resources.subnet import Subnet
from spotty.providers.aws.aws_resources.vpc import Vpc
from spotty.providers.aws.config.instance_config import InstanceConfig
from spotty.providers.aws.deployment.project_resources.key_pair import KeyPairResource


class AbstractAwsDeployment(ABC):

    def __init__(self, project_name: str, instance_config: InstanceConfig):
        self._project_name = project_name
        self._instance_config = instance_config
        self._ec2 = boto3.client('ec2', region_name=instance_config.region)

    @property
    def instance_config(self) -> InstanceConfig:
        return self._instance_config

    @property
    @abstractmethod
    def ec2_instance_name(self) -> str:
        """Name for EC2 instance."""
        raise NotImplementedError

    @property
    def key_pair(self) -> KeyPairResource:
        return KeyPairResource(self._project_name, self.instance_config.region)

    def get_vpc_id(self) -> str:
        """Returns VPC ID that should be used for deployment."""
        if self.instance_config.subnet_id:
            vpc_id = Subnet.get_by_id(self._ec2, self.instance_config.subnet_id).vpc_id
        else:
            default_vpc = Vpc.get_default_vpc(self._ec2)
            if not default_vpc:
                raise ValueError('Default VPC not found')

            vpc_id = default_vpc.vpc_id

        return vpc_id

    def get_ami(self) -> Image:
        if self.instance_config.ami_id:
            image = Image.get_by_id(self._ec2, self.instance_config.ami_id)
        else:
            image = Image.get_by_name(self._ec2, self.instance_config.ami_name)

        return image
