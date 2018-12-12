class InstanceNotRunningError(Exception):
    def __init__(self, instance_name: str):
        super().__init__('Instance "%s" is not running.\n'
                         'Use the "spotty start %s" command to start the instance.'
                         % (instance_name, instance_name))
