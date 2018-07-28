from schema import Schema, And, Use, Optional, SchemaError, Or, Regex

AMI_REGEX = r'^[\w\(\)\[\]\s\.\/\'@-]{3,128}$'


def _validate(schema: Schema, data):
    try:
        validated = schema.validate(data)
    except SchemaError as e:
        raise ValueError(e.errors[-1] if e.errors[-1] else e.autos[-1])

    return validated


def validate_instance_config(data):
    schema = Schema({
        'project': {
            'name': And(str, Regex(r'^[a-zA-Z0-9-]{1,28}$')),
            'remoteDir': And(str, Use(lambda x: x.rstrip('/'))),
            Optional('syncFilters', default=[]): [{
                Optional('exclude'): [And(str, len)],
                Optional('include'): [And(str, len)],
            }]
        },
        'instance': {
            'region': And(str, len),
            'instanceType': And(str, len),
            'amiName': And(str, len, Regex(AMI_REGEX)),
            Optional('keyName'): str,
            Optional('maxPrice'): And(Or(int, float), lambda x: x > 0),
            'volumes': And([{
                    Optional('snapshotName', default=''): str,
                    'directory': And(str, Use(lambda x: x.rstrip('/'))),
                    Optional('size', default=0): And(int, lambda x: x > 0),
                    Optional('deleteOnTermination', default=False): bool,
                }],
                And(len, error='Volume configuration is required.'),
                And(lambda x: len(x) == 1, error='Only one volume is supported at the moment.'),
            ),
            'docker': And({
                    Optional('image', default=''): str,
                    Optional('file', default=''): str,
                    Optional('dataRoot', default=''): And(str, Use(lambda x: x.rstrip('/'))),
                },
                And(lambda x: x['image'] or x['file'], error='Either "image" or "file" should be specified.'),
                And(lambda x: not (x['image'] and x['file']), error='"image" and "file" cannot be specified together.'),
            ),
            Optional('ports', default=[]): [And(int, lambda x: 0 <= x <= 65535)],
        },
        Optional('scripts'): {
            str: And(str, len),
        },
    })

    return _validate(schema, data)


def validate_ami_config(data):
    schema = Schema({
        'instance': {
            'region': And(str, len),
            'instanceType': And(str, len),
            'amiName': And(str, len, Regex(AMI_REGEX)),
            Optional('keyName'): str,
        },
    }, ignore_extra_keys=True)

    return _validate(schema, data)
