class InstanceNotRunningError(Exception):
    def __init__(self):
        super().__init__('Instance is not running.\n'
                         'Use "spotty status" command to check the current state of the instance.')
