import os
import time
import chevron
from spotty.deployment.utils.commands import get_script_command
from spotty.deployment.container.docker.scripts.abstract_docker_script import AbstractDockerScript


class StartContainerScript(AbstractDockerScript):

    def _partials(self) -> dict:
        return {
            'before_image_build': '',
            'before_container_run': '',
            'before_startup_commands': '',
        }

    def render(self, print_trace: bool = False) -> str:
        # read template file
        template_path = os.path.join(os.path.dirname(__file__), 'data', 'start_container.sh.tpl')
        with open(template_path) as f:
            template = f.read()

        # generate "docker build" command if necessary
        if self.commands.instance_config.dockerfile_path:
            image_name = '%s:%d' % (self.commands.instance_config.full_container_name, time.time())
            build_image_cmd = self.commands.build(image_name)
            pull_image_cmd = ''
        else:
            image_name = self.commands.instance_config.container_config.image
            build_image_cmd = ''
            pull_image_cmd = self.commands.pull()

        # generate a command to run the startup script
        exec_script_cmd = ''
        if self.commands.instance_config.container_config.commands:
            startup_script_cmd = get_script_command('container-startup-commands',
                                                    self.commands.instance_config.container_config.commands)
            exec_script_cmd = self.commands.exec(startup_script_cmd, user='root')

        # render the script
        content = chevron.render(template, data={
            'bash_flags': 'set -xe' if print_trace else 'set -e',
            'is_created_cmd': self.commands.is_created(),
            'remove_cmd': self.commands.remove(),
            'build_image_cmd': build_image_cmd,
            'pull_image_cmd': pull_image_cmd,
            'tmp_container_dir': self.commands.instance_config.host_container_dir,
            'start_container_cmd': self.commands.run(image_name),
            'docker_exec_startup_script_cmd': exec_script_cmd,
        }, partials_dict=self._partials())

        return content
