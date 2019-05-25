import os
import pystache
import re
from spotty.providers.gcp.config.instance_config import InstanceConfig


def prepare_image_template(instance_config: InstanceConfig, deployment_name: str, source_image_link: str):
    """Prepares deployment template to run an instance."""

    # read and update the template
    with open(os.path.join(os.path.dirname(__file__), 'image', 'template.yaml')) as f:
        template = f.read()

    # render startup script
    startup_script = open(os.path.join(os.path.dirname(__file__), 'image', 'cloud_init.yaml'), 'r').read()
    startup_script = pystache.render(startup_script, {
        'DEPLOYMENT_NAME': deployment_name,
        'IMAGE_NAME': instance_config.image_name,
        'ZONE': instance_config.zone,
    })
    indent_size = len(re.search('( *){{{STARTUP_SCRIPT}}}', template).group(1))
    startup_script = startup_script.replace('\n', '\n' + ' ' * indent_size)  # fix indent for the YAML file

    # render the template
    parameters = {
        'SERVICE_ACCOUNT_EMAIL': 'spotty@spotty-221422.iam.gserviceaccount.com',
        'ZONE': instance_config.zone,
        'MACHINE_TYPE': instance_config.machine_type,
        'SOURCE_IMAGE': source_image_link,
        'STARTUP_SCRIPT': startup_script,
        'DEPLOYMENT_NAME': deployment_name,
        'PREEMPTIBLE': 'false' if instance_config.on_demand else 'true',
        'GPU_TYPE': instance_config.gpu['type'],
        'GPU_COUNT': instance_config.gpu['count'],
    }
    template = pystache.render(template, parameters)

    return template
