import os
import chevron


def prepare_instance_profile_template(managed_policy_arns: list):
    with open(os.path.join(os.path.dirname(__file__), 'data', 'template.yaml')) as f:
        content = f.read()

    parameters = {
        'HAS_MANAGED_POLICIES': len(managed_policy_arns),
        'MANAGED_POLICY_ARNS': [{'MANAGED_POLICY_ARN': arn} for arn in managed_policy_arns]
    }

    template = chevron.render(content, parameters)

    return template
