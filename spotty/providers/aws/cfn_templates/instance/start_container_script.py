from spotty.deployment.container.docker.scripts.start_container_script import StartContainerScript


class StartContainerScriptWithCfnSignals(StartContainerScript):

    @staticmethod
    def _get_signal_command(resource_name: str):
        return 'cfn-signal -e 0 --stack $_{AWS::StackName} --region $_{AWS::Region} --resource ' + resource_name

    def _partials(self) -> dict:
        return {
            'before_image_build': self._get_signal_command('BuildingDockerImageSignal'),
            'before_container_run': self._get_signal_command('StartingContainerSignal'),
            'before_startup_commands': self._get_signal_command('RunningContainerStartupCommandsSignal'),
        }

    def render(self, print_trace: bool = False) -> str:
        content = super().render(print_trace=print_trace)
        content = content.replace('${', '${!')
        content = content.replace('$_{', '${')

        return content
