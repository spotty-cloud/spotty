from spotty.providers.aws.config.instance_config import DEFAULT_AMI_NAME
from spotty.providers.aws.resources.image import Image


def get_ami(ec2, ami_id: str = None, ami_name: str = None) -> Image:
    """Returns an AMI that should be used for deployment.

    Raises:
        ValueError: If an AMI not found.
    """
    if ami_id:
        # get an AMI by ID if the "amiId" parameter is specified
        image = Image.get_by_id(ec2, ami_id)
        if not image:
            raise ValueError('AMI with ID=%s not found.' % ami_id)
    elif ami_name:
        # get an AMI by name if the "amiName" parameter is specified
        image = Image.get_by_name(ec2, ami_name)
        if not image:
            # if an AMI name was explicitly specified in the config, but the AMI was not found, raise an error
            raise ValueError('AMI with the name "%s" was not found.' % ami_name)
    else:
        # if the "amiName" parameter is not specified, try to use the default AMI name
        image = Image.get_by_name(ec2, DEFAULT_AMI_NAME)
        if not image:
            # get the latest "Deep Learning Base AMI"
            res = ec2.describe_images(
                Owners=['amazon'],
                Filters=[{'Name': 'name', 'Values': ['Deep Learning AMI (Ubuntu 16.04) Version*']}],
            )

            if not len(res['Images']):
                raise ValueError('AWS Deep Learning AMI not found.\n'
                                 'Use the "spotty aws create-ami" command to create an AMI with NVIDIA Docker.')

            image_info = sorted(res['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]
            image = Image(ec2, image_info)

    return image
