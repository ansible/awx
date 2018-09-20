import re
import six
import yaml
import json


__all__ = ['safe_dump', 'SafeLoader', 'VaultDecoder']



class VaultData:
    def __init__(self, value):
        self.value = value


class VaultDecoder(json.JSONDecoder):
    """
    Use with JSON loader to produce vault objects where __ansible_vault
    syntax is used by user to indicate encrypted content
    ex:
        json.loads(JSON_DATA, cls=VaultDecoder)
    """
    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.object_hook
        super(VaultDecoder, self).__init__(*args, **kwargs)

    def object_hook(self, pairs):
        for key in pairs:
            value = pairs[key]
            if key == '__ansible_vault':
                return VaultData(value)

        return pairs


class VaultEncoder(json.JSONEncoder):
    """
    Use with JSON dumper to produce content with __ansible_vault
    syntax when given python data that has the vault class in it
    ex:
        json.dumps(data, cls=VaultEncoder, indent=4)
    """
    def default(self, o):
        if isinstance(o, VaultData):
            return {'__ansible_vault': o.value}
        return json.JSONEncoder.default(self, o)


class SafeStringDumper(yaml.SafeDumper):

    def represent_data(self, value):
        if isinstance(value, six.string_types):
            return self.represent_scalar('!unsafe', value)
        return super(SafeStringDumper, self).represent_data(value)

    def represent_vault_data(self, data):
        return self.represent_scalar('!vault', data.value, style='|')


class SafeLoader(yaml.Loader):

    def construct_yaml_unsafe(self, node):
        class UnsafeText(six.text_type):
            __UNSAFE__ = True
        node = UnsafeText(self.construct_scalar(node))
        return node

    def construct_yaml_vault(self, node):
        value = self.construct_scalar(node)
        return VaultData(value)



SafeLoader.add_constructor(
    u'!unsafe',
    SafeLoader.construct_yaml_unsafe
)


SafeLoader.add_constructor(
    u'!vault',
    SafeLoader.construct_yaml_vault
)


SafeStringDumper.add_representer(
    VaultData,
    SafeStringDumper.represent_vault_data
)


def safe_dump(x, safe_dict=None):
    """
    Used to serialize an extra_vars dict to YAML

    By default, extra vars are marked as `!unsafe` in the generated yaml
    _unless_ they've been deemed "trusted" (meaning, they likely were set/added
    by a user with a high level of privilege).

    This function allows you to pass in a trusted `safe_dict` to whitelist 
    certain extra vars so that they are _not_ marked as `!unsafe` in the
    resulting YAML.  Anything _not_ in this dict will automatically be
    `!unsafe`.

    safe_dump({'a': 'b', 'c': 'd'}) -> 
    !unsafe 'a': !unsafe 'b'
    !unsafe 'c': !unsafe 'd'

    safe_dump({'a': 'b', 'c': 'd'}, safe_dict={'a': 'b'})
    a: b
    !unsafe 'c': !unsafe 'd'
    """
    if isinstance(x, dict):
        yamls = []
        safe_dict = safe_dict or {}

        # Compare the top level keys so that we can find values that have
        # equality matches (and consider those branches safe)
        for k, v in x.items():
            dumper = yaml.SafeDumper
            if k not in safe_dict or safe_dict.get(k) != v:
                dumper = SafeStringDumper
            yamls.append(yaml.dump_all(
                [{k: v}],
                None,
                Dumper=dumper,
                default_flow_style=False,
            ))
        return ''.join(yamls)
    else:
        return yaml.dump_all([x], None, Dumper=SafeStringDumper, default_flow_style=False)


def sanitize_jinja(arg):
    """
    For some string, prevent usage of Jinja-like flags
    """
    if isinstance(arg, six.string_types):
        # If the argument looks like it contains Jinja expressions
        # {{ x }} ...
        if re.search(r'\{\{[^}]+}}', arg) is not None:
            raise ValueError('Inline Jinja variables are not allowed.')
        # If the argument looks like it contains Jinja statements/control flow...
        # {% if x.foo() %} ...
        if re.search(r'\{%[^%]+%}', arg) is not None:
            raise ValueError('Inline Jinja variables are not allowed.')
    return arg
