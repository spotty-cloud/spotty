import subprocess


def get_ssh_command(host: str, port: int, user: str, key_path: str, remote_cmd: list, env_vars: dict = None,
                    quiet: bool = False) -> list:
    ssh_command = ['ssh', '-ti', key_path, '-o', 'StrictHostKeyChecking no']

    if port != 22:
        ssh_command += ['-p', str(port)]

    if quiet:
        ssh_command += ['-q']

    # export environmental variables
    if env_vars:
        for var_name, value in env_vars.items():
            remote_cmd = ['export', '%s=%s' % (var_name, value), ';'] + remote_cmd

    ssh_command += ['%s@%s' % (user, host), subprocess.list2cmdline(remote_cmd)]

    return ssh_command
