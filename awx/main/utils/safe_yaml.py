import re
import yaml


__all__ = ['safe_dump', 'SafeLoader']


class SafeStringDumper(yaml.SafeDumper):

    def represent_data(self, value):
        if isinstance(value, str):
            return self.represent_scalar('!unsafe', value)
        return super(SafeStringDumper, self).represent_data(value)


class SafeLoader(yaml.Loader):

    def construct_yaml_unsafe(self, node):
        class UnsafeText(str):
            __UNSAFE__ = True
        node = UnsafeText(self.construct_scalar(node))
        return node


SafeLoader.add_constructor(
    u'!unsafe',
    SafeLoader.construct_yaml_unsafe
)


def safe_dump(x, safe_dict=None):
    """
    Used to serialize an extra_vars dict to YAML

    By default, extra vars are marked as `!unsafe` in the generated yaml
    _unless_ they've been deemed "trusted" (meaning, they likely were set/added
    by a user with a high level of privilege).

    This function allows you to pass in a trusted `safe_dict` to allow
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
    if isinstance(arg, str):
        # If the argument looks like it contains Jinja expressions
        # {{ x }} ...
        if re.search(r'\{\{[^}]+}}', arg) is not None:
            raise ValueError('Inline Jinja variables are not allowed.')
        # If the argument looks like it contains Jinja statements/control flow...
        # {% if x.foo() %} ...
        if re.search(r'\{%[^%]+%}', arg) is not None:
            raise ValueError('Inline Jinja variables are not allowed.')
    return arg
