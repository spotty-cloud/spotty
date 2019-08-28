class ImageNotFoundError(Exception):
    def __init__(self, image_name):
        super().__init__('The image "%s" was not found.\n'
                         'Use the "spotty gcp create-image" command to create an image with NVIDIA Docker.'
                         % image_name)
