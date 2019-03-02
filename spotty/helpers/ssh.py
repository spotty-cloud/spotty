import base64
import subprocess


def get_ssh_command(host: str, port: int, user: str, key_path: str, remote_cmd: str, quiet: bool = False) -> list:
    ssh_command = ['ssh', '-ti', key_path, '-o', 'StrictHostKeyChecking no']

    if port != 22:
        ssh_command += ['-p', str(port)]

    if quiet:
        ssh_command += ['-q']

    ssh_command += ['%s@%s' % (user, host), remote_cmd]

    return ssh_command


def run_script(host: str, port: int, user: str, key_path: str, script_name: str, script_content: str,
               tmux_session_name: str, restart: bool = False, logging: bool = False):
    # encode the script content to base64
    script_base64 = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')

    # a remote path where the script will be uploaded
    instance_script_path = '/tmp/spotty/container/scripts/run/%s.sh' % script_name
    container_script_path = '/tmp/scripts/run/%s.sh' % script_name

    # command to attach user to existing tmux session
    attach_session_cmd = subprocess.list2cmdline(['tmux', 'attach', '-t', tmux_session_name, '>', '/dev/null',
                                                  '2>&1'])

    # command to kill session in case of a restart
    kill_session_cmd = subprocess.list2cmdline(['tmux', 'kill-session', '-t', tmux_session_name, '>', '/dev/null',
                                                '2>&1'])

    # command to upload user script to the instance
    upload_script_cmd = subprocess.list2cmdline(['echo', script_base64, '|', 'base64', '-d', '>', instance_script_path])

    # log the script outputs to the file
    log_cmd = ['2>&1', '|', 'tee', '/var/log/spotty/run/%s-`date +%%s`.log' % script_name] if logging else []

    # command to run user script inside the docker container
    docker_cmd = subprocess.list2cmdline(['sudo', '/tmp/spotty/instance/scripts/container_bash.sh', '-xe',
                                          container_script_path] + log_cmd)

    # command to create new tmux session and run user script
    new_session_cmd = subprocess.list2cmdline(['tmux', 'new', '-s', tmux_session_name, '-n', script_name,
                                               'tmux set remain-on-exit on && %s' % docker_cmd])

    if restart:
        # composition of the commands: killing the script session if it already exists, then uploading the script
        # to the instance, creating new tmux session and running the script inside the Docker container
        remote_cmd = '%s; (%s && %s)' % (kill_session_cmd, upload_script_cmd, new_session_cmd)
    else:
        # composition of the commands: trying to attach the user to the existing tmux session. If it doesn't exist,
        # uploading the user script to the instance, creating new tmux session and running that script
        # inside the Docker container
        remote_cmd = '%s || (%s && %s)' % (attach_session_cmd, upload_script_cmd, new_session_cmd)

    # connect to the instance and run the command
    ssh_command = get_ssh_command(host, port, user, key_path, remote_cmd)
    subprocess.call(ssh_command)
