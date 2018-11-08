from spotty.project_resources.key_pair import KeyPairResource


def get_ssh_command(project_name: str, region: str, host: str, remote_cmd: str, local_ssh_port: None,
                    quiet: bool = False) -> list:
    ssh_port = 22
    user = 'ubuntu'

    if local_ssh_port:
        ssh_port = local_ssh_port
        host = '127.0.0.1'

    key_path = KeyPairResource(None, project_name, region).key_path

    ssh_command = ['ssh', '-p', str(ssh_port), '-i', key_path, '-o', 'StrictHostKeyChecking no', '-t']
    if quiet:
        ssh_command += ['-q']

    ssh_command += ['%s@%s' % (user, host), remote_cmd]

    return ssh_command
