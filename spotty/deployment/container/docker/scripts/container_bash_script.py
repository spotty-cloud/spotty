import os
import chevron
from spotty.deployment.utils.commands import get_bash_command
from spotty.deployment.container.docker.scripts.abstract_docker_script import AbstractDockerScript


class ContainerBashScript(AbstractDockerScript):

    def render(self) -> str:
        # read template file
        template_path = os.path.join(os.path.dirname(__file__), 'data', 'container_bash.sh.tpl')
        with open(template_path) as f:
            template = f.read()

        # render the script
        content = chevron.render(template, data={
            'docker_exec_bash': self.commands.exec(get_bash_command(), interactive=True, tty=True,
                                                   container_name='$SPOTTY_CONTAINER_NAME',
                                                   working_dir='$SPOTTY_CONTAINER_WORKING_DIR'),
        })

        return content
