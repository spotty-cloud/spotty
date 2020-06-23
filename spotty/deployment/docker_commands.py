import os
import subprocess
from spotty.deployment.file_structure import CONTAINER_RUN_SCRIPTS_DIR


def get_bash_cmd(container_name: str, working_dir: str = None) -> list:
    # start bash in the docker container
    working_dir_params = ['-w', working_dir] if working_dir else []
    docker_exec_cmd = ['docker', 'exec', '-it', *working_dir_params, container_name, '/usr/bin/env', 'bash']

    return docker_exec_cmd


def get_script_cmd(container_name: str, script_name: str, script_base64: str, script_args: list = None,
                   working_dir: str = None, log_file_path: str = None) -> list:
    # command to decode the script, save it to a temporary file and run inside the container
    tmp_script_path = '%s/%s' % (CONTAINER_RUN_SCRIPTS_DIR, script_name)
    script_args = script_args if script_args else []
    container_cmd = subprocess.list2cmdline([
        'mkdir', '-p', CONTAINER_RUN_SCRIPTS_DIR,
        '&&', 'echo', script_base64, '|', 'base64', '-d', '>', tmp_script_path,
        '&&', 'chmod', '+x', tmp_script_path,
        '&&', tmp_script_path, *script_args,
    ])

    # execute the script in the docker container
    docker_exec_cmd = get_bash_cmd(container_name, working_dir) + ['-c', container_cmd]

    # log the script outputs to a file on the host OS
    if log_file_path:
        log_dir = os.path.dirname(log_file_path)
        docker_exec_cmd = [
            'set', '-o', 'pipefail', ';',
            'mkdir', '-p', log_dir,
            '&&', *docker_exec_cmd, '2>&1', '|', 'tee', log_file_path,
        ]

    return docker_exec_cmd
