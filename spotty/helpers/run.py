import re
import chevron
from chevron.tokenizer import tokenize


def parse_parameters(script_params: str):
    """Parses script parameters."""
    params = {}
    for param in script_params:
        match = re.match('(\w+)=(.*)', param)
        if not match:
            raise ValueError('Invalid script parameter: "%s"' % param)

        param_name, param_value = match.groups()
        if param_name in params:
            raise ValueError('Parameter "%s" defined twice' % param_name)

        params[param_name] = param_value

    return params


def render_script(template: str, params: dict):
    """Renders a script template.

    It based on the Mustache templates, but only
    variables and delimiter changes are allowed.

    Raises an exception if one of the provided parameters doesn't
    exist in the template.
    """
    tokens = list(tokenize(template))
    template_keys = set()
    for tag, key in tokens:
        if tag not in ['literal', 'no escape', 'variable', 'set delimiter']:
            raise ValueError('Script templates support only variables and delimiter changes.')

        template_keys.add(key)

    # check that the script contains keys for all provided parameters
    for key in params:
        if key not in template_keys:
            raise ValueError('Parameter "%s" doesn\'t exist in the script.' % key)

    return chevron.render(tokens, params)
