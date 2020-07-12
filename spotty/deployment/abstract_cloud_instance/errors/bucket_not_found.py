class BucketNotFoundError(Exception):
    def __init__(self):
        super().__init__('Bucket for the project not found.')
