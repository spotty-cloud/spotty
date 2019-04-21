from spotty.commands.writers.abstract_output_writrer import AbstractOutputWriter
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.providers.gcp.gcp_resources.image import Image
from spotty.providers.gcp.helpers.ce_client import CEClient
from spotty.providers.gcp.helpers.deployment import wait_resources
from spotty.providers.gcp.helpers.dm_client import DMClient


class ImageDeployment(object):

    def __init__(self, instance_config: InstanceConfig):
        self._instance_config = instance_config
        self._compute_client = CEClient(instance_config.project_id, instance_config.zone)
        self._dm_client = DMClient(instance_config.project_id, instance_config.zone)

    @property
    def compute_client(self) -> CEClient:
        return self._compute_client

    @property
    def instance_config(self) -> InstanceConfig:
        return self._instance_config

    def get_image(self) -> Image:
        return Image.get_by_name(self._compute_client, self.instance_config.image_name)

    def deploy(self, key_name, keep_instance: bool, output: AbstractOutputWriter, dry_run=False):
        # check that it's a GPU instance type
        if not self.instance_config.gpu:
            raise ValueError('Instance with GPU is required to create an image with NVIDIA Docker')

        # check GPU type
        accelerator_types = self._compute_client.get_accelerator_types()
        gpu_type = self.instance_config.gpu['type']
        if gpu_type not in accelerator_types:
            raise ValueError('GPU type "%s" is not supported in the "%s" zone.\nAvailable GPU types are: %s.' %
                             (gpu_type, self.instance_config.zone, ', '.join(accelerator_types.keys())))
        # TODO: gpu count check

        if keep_instance and not key_name:
            output.write('Key Pair name is not specified, you will not be able to connect to the instance.')

        # # check that an image with this name doesn't exist yet
        # image = self.get_image()
        # if image:
        #     raise ValueError('Image with the name "%s" already exists.' % image.name)

        # create stack
        deployment_name = 'spotty-image-%s' % self.instance_config.image_name.lower()
        res = self._dm_client.get(deployment_name)
        if res:
            raise ValueError('Deployment "%s" already exists.' % deployment_name)

        # get the latest Ubuntu 16.04 image
        compute = self.compute_client.compute
        image_data = compute.images().getFromFamily(project='ubuntu-os-cloud', family='ubuntu-1604-lts').execute()
        image = Image(image_data)

        # prepare deployment template
        from spotty.providers.gcp.deployment.dm_templates.image_template import prepare_image_template
        template = prepare_image_template(self.instance_config, deployment_name, image.self_link)

        # TODO: OnFailure='DO_NOTHING' if keep_instance else 'DELETE',
        self._dm_client.deploy(deployment_name, template, dry_run)

        output.write('Waiting for the image to be created...')

        deployment_name = 'spotty-image-%s' % self.instance_config.image_name.lower() # TMP
        resource_messages = {
            '%s-instance' % deployment_name: 'launching the instance',
            '%s-docker-waiter' % deployment_name: 'installing NVIDIA Docker',
            '%s-image-waiter' % deployment_name: 'creating the image and terminating the instance',
        }

        # wait for the stack to be created
        with output.prefix('  '):
            wait_resources(self._dm_client, deployment_name, resource_messages, output)

        output.write('\n'
                     '--------------------------------------------------\n'
                     'Image "%s" was successfully created.\n'
                     'Use the "spotty start" command to run an instance.\n'
                     '--------------------------------------------------'
                     % self.instance_config.image_name)
