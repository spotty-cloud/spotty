import os
import chevron
from spotty.deployment.container_scripts.docker.abstract_docker_script import AbstractDockerScript


class StopContainerScript(AbstractDockerScript):

    def render(self) -> str:
        # read template file
        template_path = os.path.join(os.path.dirname(__file__), 'data', 'stop_container.sh.tpl')
        with open(template_path) as f:
            template = f.read()

        # render the script
        content = chevron.render(template, data={
            'container_name': self.commands.instance_config.full_container_name,
        })

        return content
