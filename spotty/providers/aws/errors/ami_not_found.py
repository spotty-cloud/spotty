class AmiNotFoundError(Exception):
    def __init__(self, ami_name):
        super().__init__('The AMI "%s" was not found.\n'
                         'Use the "spotty aws create-ami" command to create an AMI with NVIDIA Docker.'
                         % ami_name)
