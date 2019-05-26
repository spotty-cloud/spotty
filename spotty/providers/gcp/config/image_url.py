import re


IMAGE_URL_REGEX = '^(?:projects/([a-z](?:[-a-z0-9]*[a-z0-9])?)/)?' \
                  'global/images/(family/)?([a-z](?:[-a-z0-9]*[a-z0-9])?)$'


class ImageUrl(object):

    def __init__(self, image_url: str):
        res = re.match(IMAGE_URL_REGEX, image_url)
        if not res:
            raise ValueError('Image URL has a wrong format')

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
