import unittest
from spotty.providers.aws.config.validation import validate_instance_parameters


class TestBucketResource(unittest.TestCase):

    def test_default_configuration(self):
        required_params = {
            'region': 'eu-west-1',
            'instanceType': 'p2.xlarge',
        }

        expected_params = {
            **required_params,
            'amiName': 'SpottyAMI',
            'availabilityZone': '',
            'dockerDataRoot': '',
            'localSshPort': None,
            'maxPrice': 0,
            'onDemandInstance': False,
            'rootVolumeSize': 0,
            'subnetId': '',
            'volumes': [],
        }

        self.assertEqual(expected_params, validate_instance_parameters(required_params))

    def test_failed_validation(self):
        # no params
        with self.assertRaises(ValueError):
            validate_instance_parameters({})

        # wrong case for the region
        with self.assertRaises(ValueError):
            validate_instance_parameters({
                'region': 'EU-WEST-1',
                'instanceType': 'p2.xlarge',
            })

        # unknown parameter
        with self.assertRaises(ValueError):
            validate_instance_parameters({
                'region': 'eu-west-1',
                'instanceType': 'p2.xlarge',
                'unknownParameter': 'test',
            })


if __name__ == '__main__':
    unittest.main()
