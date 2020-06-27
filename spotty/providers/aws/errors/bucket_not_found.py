class BucketNotFoundError(Exception):
    def __init__(self):
        super().__init__('An S3 bucket for the project not found.')
