from spotty.providers.gcp.config.instance_config import DEFAULT_IMAGE_NAME
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.resources.image import Image


def get_image(ce: CEClient, image_uri: str = None, image_name: str = None) -> Image:
    """Returns an image that should be used for deployment.

    Raises:
        ValueError: If an image not found.
    """
    if image_uri:
        # get an image by its URL if the "imageUri" parameter is specified
        image = Image.get_by_uri(ce, image_uri)
        if not image:
            raise ValueError('Image "%s" not found.' % image_uri)
    elif image_name:
        # get an image by name if the "imageName" parameter is specified
        image = Image.get_by_name(ce, image_name)
        if not image:
            # if an image name was explicitly specified, but the image was not found, raise an error
            raise ValueError('Image with the name "%s" was not found.' % image_name)
    else:
        # if the "imageName" parameter is not specified, try to use the default image name
        image = Image.get_by_name(ce, DEFAULT_IMAGE_NAME)
        if not image:
            # get the latest "common-gce-gpu-image" image
            image_family_url = 'projects/ml-images/global/images/family/common-gce-gpu-image'
            image = Image.get_by_uri(ce, image_family_url)
            if not image:
                raise ValueError('The "common-gce-gpu-image" image was not found.')

    return image
