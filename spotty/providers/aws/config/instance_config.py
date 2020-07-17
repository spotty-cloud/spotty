from typing import List
from spotty.config.abstract_instance_config import AbstractInstanceConfig, VolumeMount
from spotty.config.abstract_instance_volume import AbstractInstanceVolume
from spotty.providers.aws.config.validation import validate_instance_parameters
from spotty.providers.aws.config.ebs_volume import EbsVolume


DEFAULT_AMI_NAME = 'SpottyAMI'


class InstanceConfig(AbstractInstanceConfig):

    def _validate_instance_params(self, params: dict) -> dict:
        return validate_instance_parameters(params)

    def _get_instance_volumes(self) -> List[AbstractInstanceVolume]:
        volumes = []
        for volume_config in self._params['volumes']:
            volume_type = volume_config['type']
            if volume_type == EbsVolume.TYPE_NAME:
                volumes.append(EbsVolume(volume_config, self.project_config.project_name, self.name))
            else:
                raise ValueError('AWS volume type "%s" not supported.' % volume_type)

        return volumes

    @property
    def user(self):
        return 'ubuntu'

    @property
    def ec2_instance_name(self) -> str:
        return '%s-%s' % (self.project_config.project_name.lower(), self.name.lower())

    @property
    def region(self) -> str:
        return self._params['region']

    @property
    def availability_zone(self) -> str:
        return self._params['availabilityZone']

    @property
    def subnet_id(self) -> str:
        return self._params['subnetId']

    @property
    def instance_type(self) -> str:
        return self._params['instanceType']

    @property
    def is_spot_instance(self) -> bool:
        return self._params['spotInstance']

    @property
    def ami_name(self) -> str:
        return self._params['amiName']

    @property
    def ami_id(self) -> str:
        return self._params['amiId']

    @property
    def root_volume_size(self) -> int:
        return self._params['rootVolumeSize']

    @property
    def ports(self) -> List[int]:
        return list(set(self._params['ports']))

    @property
    def max_price(self) -> float:
        return self._params['maxPrice']

    @property
    def managed_policy_arns(self) -> list:
        return self._params['managedPolicyArns']
    
    @property
    def instance_profile_arn(self) -> str:
        return self._params['instanceProfileArn']
