from spotty.config.abstract_instance_config import AbstractInstanceConfig
from spotty.providers.aws.config.validation import validate_instance_parameters

VOLUME_TYPE_EBS = 'ebs'


class InstanceConfig(AbstractInstanceConfig):

    def __init__(self, config: dict):
        super().__init__(config)

        self._params = validate_instance_parameters(self._params)

        # set the default volume type value
        for volume in self._params['volumes']:
            if not volume['type']:
                volume['type'] = VOLUME_TYPE_EBS

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
    def on_demand(self) -> bool:
        return self._params['onDemandInstance']

    @property
    def ami_name(self) -> str:
        return self._params['amiName']

    @property
    def root_volume_size(self) -> int:
        return self._params['rootVolumeSize']

    @property
    def docker_data_root(self) -> int:
        return self._params['dockerDataRoot']

    @property
    def max_price(self) -> float:
        return self._params['maxPrice']
