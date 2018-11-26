class InstanceNotRunningError(Exception):
    def __init__(self):
        super().__init__('Instance is not running.\n'
                         'Use "spotty start" command to start an instance.')
