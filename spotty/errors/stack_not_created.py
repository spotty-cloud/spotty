class StackNotCreatedError(Exception):
    def __init__(self):
        super().__init__('Instance is not started.\n'
                         'Use "spotty start" command to start the instance.')
