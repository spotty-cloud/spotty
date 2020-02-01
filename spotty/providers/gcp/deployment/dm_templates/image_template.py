import os
import chevron
from spotty.providers.gcp.config.instance_config import InstanceConfig
from spotty.utils import fix_indents_for_lines


def prepare_image_template(instance_config: InstanceConfig, machine_name: str, scr_image_link: str, image_family: str,
                           service_account_email: str, stack_version: str, public_key_value: str = '',
                           debug_mode: bool = False):
    """Prepares deployment template to run an instance."""

    # read and update the template
    with open(os.path.join(os.path.dirname(__file__), 'image', 'template.yaml')) as f:
        template = f.read()

    # render startup script
    startup_script = open(os.path.join(os.path.dirname(__file__), 'image', 'cloud_init.yaml'), 'r').read()
    startup_script = chevron.render(startup_script, {
        'MACHINE_NAME': machine_name,
        'ZONE': instance_config.zone,
        'IMAGE_NAME': instance_config.image_name,
        'IMAGE_FAMILY': image_family if image_family else '',
        'STACK_VERSION': stack_version,
        'NVIDIA_DRIVER_VERSION': '410',
        'DOCKER_CE_VERSION': '19.03.5',
        'CONTAINERD_IO_VERSION': '1.2.10-3',
        'NVIDIA_CONTAINER_TOOLKIT_VERSION': '1.0.5-1',
        'DEBUG_MODE': debug_mode,
    })

    # render the template
    parameters = {
        'SERVICE_ACCOUNT_EMAIL': service_account_email,
        'ZONE': instance_config.zone,
        'MACHINE_TYPE': instance_config.machine_type,
        'MACHINE_NAME': machine_name,
        'SOURCE_IMAGE': scr_image_link,
        'IMAGE_NAME': instance_config.image_name,
        'STARTUP_SCRIPT': fix_indents_for_lines(startup_script, template, '{{{STARTUP_SCRIPT}}}'),
        'PREEMPTIBLE': 'false' if instance_config.on_demand else 'true',
        'GPU_TYPE': instance_config.gpu['type'],
        'GPU_COUNT': instance_config.gpu['count'],
        'PUB_KEY_VALUE': public_key_value,
        'DEBUG_MODE': debug_mode,
    }
    template = chevron.render(template, parameters)

    return template
