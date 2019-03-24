class VolumeNotFoundError(Exception):
    def __init__(self, volume_name):
        super().__init__('Volume "%s" not found' % volume_name)
