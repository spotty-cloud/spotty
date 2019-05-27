from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.deployment.abstract_gcp_deployment import AbstractGcpDeployment
from spotty.providers.gcp.deployment.project_resources.image_stack import ImageStack
from spotty.providers.gcp.gcp_resources.image import Image
from spotty.providers.gcp.gcp_resources.instance import Instance


class ImageDeployment(AbstractGcpDeployment):

    # version of the image stack
    VERSION = '1.0.0'

    @property
    def machine_name(self) -> str:
        return 'spotty-image-%s' % self.instance_config.image_name.lower()

    @property
    def stack(self):
        return ImageStack(self.instance_config.image_name, self._credentials.project_id, self.instance_config.zone)

    def deploy(self, image_family: str, debug_mode: bool, output: AbstractOutputWriter):
        # check that the "amiId" parameter is not set
        if self.instance_config.image_url:
            raise ValueError('The "imageUrl" parameter cannot be used when creating an image.')

        # check that it's an instance with GPU
        if not self.instance_config.gpu:
            raise ValueError('Instance with GPU is required to create an image with NVIDIA Docker')

        # check GPU type
        accelerator_types = self._ce.get_accelerator_types()
        gpu_type = self.instance_config.gpu['type']
        if gpu_type not in accelerator_types:
            raise ValueError('GPU type "%s" is not supported in the "%s" zone.\nAvailable GPU types are: %s.' %
                             (gpu_type, self.instance_config.zone, ', '.join(accelerator_types.keys())))

        # TODO: gpu count check

        # check that an image with this name doesn't exist yet
        image = Image.get_by_name(self._ce, self.instance_config.image_name)
        if image:
            raise ValueError('Image with the name "%s" already exists.' % image.name)

        # get the latest Ubuntu 16.04 image
        ubuntu_family_name = 'projects/ubuntu-os-cloud/global/images/family/ubuntu-1604-lts'
        image = Image.get_by_url(self._ce, ubuntu_family_name)

        # prepare deployment template
        from spotty.providers.gcp.deployment.dm_templates.image_template import prepare_image_template
        template = prepare_image_template(self.instance_config, self.machine_name, image.self_link, image_family,
                                          self._credentials.service_account_email, self.VERSION, debug_mode=debug_mode)

        # create stack
        self.stack.create_stack(template, self.machine_name, debug_mode, output)

    def get_ip_address(self):
        instance = Instance.get_by_name(self._ce, self.machine_name)
        if not instance or not instance.is_running:
            return None

        if self._instance_config.local_ssh_port:
            return '127.0.0.1'

        return instance.public_ip_address
