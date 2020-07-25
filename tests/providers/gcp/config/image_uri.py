import unittest
from spotty.providers.gcp.config.image_uri import ImageUri


class TestImageUrl(unittest.TestCase):

    def test_image_url_parsing(self):
        pos_tests = [
            {
                'uri': 'projects/debian-cloud/global/images/family/debian-9',
                'expected': ('debian-cloud', True, 'debian-9'),
            },
            {
                'uri': 'projects/debian-cloud/global/images/debian-9-stretch',
                'expected': ('debian-cloud', False, 'debian-9-stretch'),
            },
            {
                'uri': 'global/images/family/my-image-family',
                'expected': (None, True, 'my-image-family'),
            },
            {
                'uri': 'global/images/my-custom-image',
                'expected': (None, False, 'my-custom-image'),
            },
            {
                'uri': 'https://compute.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-9-stretch',
                'expected': ('debian-cloud', False, 'debian-9-stretch'),
            },
        ]

        for pos_test in pos_tests:
            image_uri = ImageUri(pos_test['uri'])
            self.assertEqual(pos_test['expected'], (image_uri.project_id, image_uri.is_family, image_uri.name))

        neg_tests = [
            'projects//global/images/family/debian-9',  # no project
            'projects/test1/test2/global/images/family/debian-9',  # extra part
            'projects/debian-cloud/global/image/family/debian-9',  # "image" misspelling
            'projects/debian-cloud/global/images/family/Debian-9',  # capital letter
            'projects/debian-cloud/global/images/'  # no image name
            '/global/images/family/debian-9',  # starts with a slash
            'global/images/family/debian-9/',  # ends with a slash
            'global/images/-my-custom-image',  # image name starts with a dash
            'global/images/my-custom-image-',  # image name ends with a dash
            'https://compute.googleapis.com/compute/v1/global/images/debian-9-stretch',  # no project name
        ]

        for neg_test in neg_tests:
            with self.assertRaises(ValueError):
                ImageUri(neg_test)


if __name__ == '__main__':
    unittest.main()
