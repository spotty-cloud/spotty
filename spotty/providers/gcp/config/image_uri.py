import re


IMAGE_URI_REGEX = '^(?:(?:https://compute.googleapis.com/compute/v1/)?projects/([a-z](?:[-a-z0-9]*[a-z0-9])?)/)?' \
                  'global/images/(family/)?([a-z](?:[-a-z0-9]*[a-z0-9])?)$'


class ImageUri(object):

    def __init__(self, image_uri: str):
        res = re.match(IMAGE_URI_REGEX, image_uri)
        if not res:
            raise ValueError('Image URI has a wrong format')

        self._project_id, self._is_family, self._name = res.groups()

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def is_family(self):
        return bool(self._is_family)

    @property
    def name(self):
        """Image name or image family name."""
        return self._name
