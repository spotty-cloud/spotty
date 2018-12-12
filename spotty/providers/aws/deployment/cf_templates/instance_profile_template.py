import os


def prepare_instance_profile_template():
    with open(os.path.join(os.path.dirname(__file__), 'data', 'instance_profile.yaml')) as f:
        template = f.read()

    return template
