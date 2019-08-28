import unittest
from spotty.providers.gcp.config.image_url import ImageUrl


class TestImageUrl(unittest.TestCase):

    def test_image_url_parsing(self):
        pos_tests = [
            {
                'url': 'projects/debian-cloud/global/images/family/debian-9',
                'expected': ('debian-cloud', True, 'debian-9'),
            },
            {
                'url': 'projects/debian-cloud/global/images/debian-9-stretch',
                'expected': ('debian-cloud', False, 'debian-9-stretch'),
            },
            {
                'url': 'global/images/family/my-image-family',
                'expected': (None, True, 'my-image-family'),
            },
            {
                'url': 'global/images/my-custom-image',
                'expected': (None, False, 'my-custom-image'),
            }
        ]

        for pos_test in pos_tests:
            image_url = ImageUrl(pos_test['url'])
            self.assertEqual(pos_test['expected'], (image_url.project_id, image_url.is_family, image_url.name))

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
        ]

        for neg_test in neg_tests:
            with self.assertRaises(ValueError):
                ImageUrl(neg_test)
