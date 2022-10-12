import unittest
from spotty.providers.aws.config.validation import validate_instance_parameters


class TestBucketResource(unittest.TestCase):

    def test_default_configuration(self):
        """Checks the default values for an instance configuration are set correctly."""
        required_params = {
            'region': 'eu-west-1',
            'instanceType': 'p2.xlarge',
        }

        expected_params = {
            **required_params,
            'amiId': None,
            'amiName': None,
            'availabilityZone': '',
            'commands': '',
            'containerName': None,
            'dockerDataRoot': '',
            'instanceProfileArn': None,
            'localSshPort': None,
            'managedPolicyArns': [],
            'maxPrice': 0,
            'ports': [],
            'rootVolumeSize': 0,
            'spotInstance': False,
            'subnetId': '',
            'volumes': [],
            'inboundIp': '0.0.0.0/0',
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
