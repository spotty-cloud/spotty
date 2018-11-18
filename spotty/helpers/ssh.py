import base64
import subprocess


def get_ssh_command(host: str, user: str, key_path: str, remote_cmd: str, local_ssh_port: None,
                    quiet: bool = False) -> list:
    ssh_port = 22

    if local_ssh_port:
        ssh_port = local_ssh_port
        host = '127.0.0.1'

    ssh_command = ['ssh', '-p', str(ssh_port), '-i', key_path, '-o', 'StrictHostKeyChecking no', '-t']
    if quiet:
        ssh_command += ['-q']

    ssh_command += ['%s@%s' % (user, host), remote_cmd]

    return ssh_command


def run_script(host, user, key_path, script_name, script_content, tmux_session_name, local_ssh_port: None):
    # encode the script content to base64
    script_base64 = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')

    # remote path where the script will be uploaded
    script_path = '/tmp/docker/%s.sh' % script_name

    # log file for the script outputs
    script_log_file = '/var/log/spotty-run/%s.log' % script_name

    # command to attach user to existing tmux session
    attach_session_cmd = subprocess.list2cmdline(['tmux', 'attach', '-t', tmux_session_name, '>', '/dev/null', '2>&1'])

    # command to upload user script to the instance
    upload_script_cmd = subprocess.list2cmdline(['echo', script_base64, '|', 'base64', '-d', '>', script_path])

    # command to log the time when user script started
    start_time_cmd = subprocess.list2cmdline(['echo', '-e', '\\nScript started: `date \'+%Y-%m-%d %H:%M:%S\'`\\n',
                                              '>>', script_log_file])

    # command to run user script inside the docker container
    docker_cmd = subprocess.list2cmdline(['sudo', '/scripts/container_bash.sh', '-xe', script_path, '2>&1',
                                          '|', 'tee', '-a', script_log_file])

    # command to create new tmux session and run user script
    new_session_cmd = subprocess.list2cmdline(['tmux', 'new', '-s', tmux_session_name,
                                               '%s && %s' % (start_time_cmd, docker_cmd)])

    # composition of the commands: if user cannot be attached to the tmux session (assume the session doesn't
    # exist), then we're uploading user script to the instance, creating new tmux session and running that script
    # inside the Docker container
    remote_cmd = '%s || (%s && %s)' % (attach_session_cmd, upload_script_cmd, new_session_cmd)

    # connect to the instance and run the command
    ssh_command = get_ssh_command(host, user, key_path, remote_cmd, local_ssh_port)
    subprocess.call(ssh_command)
