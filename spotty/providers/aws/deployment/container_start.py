import base64
import subprocess
from spotty.deployment.container_deployment import ContainerDeployment
from spotty.deployment.file_structure import RUN_CONTAINER_SCRIPT_PATH, CONTAINER_STARTUP_SCRIPT_PATH
from spotty.helpers.ssh import get_ssh_command
from spotty.providers.aws.config.instance_config import InstanceConfig


def start_container(instance_config: InstanceConfig, host: str, port: int, user: str, key_path: str):
    # encode the script content to base64
    script_base64 = base64.b64encode(instance_config.container_config.commands.encode('utf-8')).decode('utf-8')

    # command to upload startup script to the instance
    upload_script_cmd = subprocess.list2cmdline(
        ['echo', script_base64, '|', 'base64', '-d', '>', instance_config.host_startup_script_path])

    # a command to run the container
    run_container_cmd = subprocess.list2cmdline([
        'sudo', '-i',
        RUN_CONTAINER_SCRIPT_PATH,
        '--container-name=' + instance_config.full_container_name,
        '--image-name=' + instance_config.container_config.image,
        '--dockerfile-path=' + instance_config.dockerfile_path,
        '--docker-context-path=' + instance_config.docker_context_path,
        '--docker-runtime-params=' + ContainerDeployment(instance_config).get_runtime_parameters(),
        '--working-dir=' + instance_config.container_config.working_dir,
        '--startup-script-path=' + CONTAINER_STARTUP_SCRIPT_PATH,
    ])

    remote_cmd = '%s & %s' % (upload_script_cmd, run_container_cmd)

    # connect to the instance and run remote command
    ssh_command = get_ssh_command(host, port, user, key_path, remote_cmd, quiet=True)
    subprocess.call(ssh_command)
