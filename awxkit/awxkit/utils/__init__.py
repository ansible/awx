from datetime import datetime, timedelta, tzinfo
import inspect
import logging
import random
import shlex
import types
import time
import sys
import re
import os

import yaml

from awxkit.words import words
from awxkit.exceptions import WaitUntilTimeout


log = logging.getLogger(__name__)


cloud_types = (
    'aws',
    'azure',
    'azure_ad',
    'azure_classic',
    'azure_rm',
    'cloudforms',
    'ec2',
    'gce',
    'openstack',
    'openstack_v2',
    'openstack_v3',
    'rhv',
    'satellite6',
    'tower',
    'vmware',
)
credential_type_kinds = ('cloud', 'net')

not_provided = 'xx__NOT_PROVIDED__xx'


def super_dir_set(cls):
    attrs = set()
    for _class in inspect.getmro(cls):
        attrs.update(dir(_class))
    return attrs


class NoReloadError(Exception):
    pass


class PseudoNamespace(dict):
    def __init__(self, _d=None, **loaded):
        if not isinstance(_d, dict):
            _d = {}
        _d.update(loaded)
        super(PseudoNamespace, self).__init__(_d)

        # Convert nested structures into PseudoNamespaces
        for k, v in _d.items():
            tuple_converted = False
            if isinstance(v, tuple):
                self[k] = v = list(v)
                tuple_converted = True

            if isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        self[k][i] = PseudoNamespace(item)
                if tuple_converted:
                    self[k] = tuple(self[k])
            elif isinstance(v, dict):
                self[k] = PseudoNamespace(v)

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise AttributeError("{!r} has no attribute {!r}".format(self.__class__.__name__, attr))

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)

    def __setitem__(self, key, value):
        if not isinstance(value, PseudoNamespace):
            tuple_converted = False
            if isinstance(value, dict):
                value = PseudoNamespace(value)
            elif isinstance(value, tuple):
                value = list(value)
                tuple_converted = True

            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict) and not isinstance(item, PseudoNamespace):
                        value[i] = PseudoNamespace(item)
                if tuple_converted:
                    value = tuple(value)

        super(PseudoNamespace, self).__setitem__(key, value)

    def __delattr__(self, attr):
        self.__delitem__(attr)

    def __dir__(self):
        attrs = super_dir_set(self.__class__)
        attrs.update(self.keys())
        return sorted(attrs)

    # override builtin in order to have updated content become
    # PseudoNamespaces if applicable
    def update(self, iterable=None, **kw):
        if iterable:
            if hasattr(iterable, 'keys') and isinstance(iterable.keys, (types.FunctionType, types.BuiltinFunctionType, types.MethodType)):
                for key in iterable:
                    self[key] = iterable[key]
            else:
                for (k, v) in iterable:
                    self[k] = v
        for k in kw:
            self[k] = kw[k]


def is_relative_endpoint(candidate):
    return isinstance(candidate, (str,)) and candidate.startswith('/api/')


def is_class_or_instance(obj, cls):
    """returns True is obj is an instance of cls or is cls itself"""
    return isinstance(obj, cls) or obj is cls


def filter_by_class(*item_class_tuples):
    """takes an arbitrary number of (item, class) tuples and returns a list consisting
    of each item if it's an instance of the class, the item if it's a (class, dict()) tuple,
    the class itself if item is truthy but not an instance of the
    class or (class, dict()) tuple, or None if item is falsy in the same order as the arguments
    ```
    _cred = Credential()
    inv, org, cred = filter_base_subclasses((True, Inventory), (None, Organization), (_cred, Credential))
    inv == Inventory
    org == None
    cred == _cred
    ```
    """
    results = []
    for item, cls in item_class_tuples:
        if item:
            was_tuple = False
            if isinstance(item, tuple):
                was_tuple = True
                examined_item = item[0]
            else:
                examined_item = item
            if is_class_or_instance(examined_item, cls) or is_proper_subclass(examined_item, cls):
                results.append(item)
            else:
                updated = (cls, item[1]) if was_tuple else cls
                results.append(updated)
        else:
            results.append(None)
    return results


def load_credentials(filename=None):
    if filename is None:
        path = os.path.join(os.getcwd(), 'credentials.yaml')
    else:
        path = os.path.abspath(filename)

    if os.path.isfile(path):
        with open(path) as credentials_fh:
            credentials_dict = yaml.safe_load(credentials_fh)
            return credentials_dict
    else:
        msg = 'Unable to load credentials file at %s' % path
        raise Exception(msg)


def load_projects(filename=None):
    if filename is None:
        return {}
    else:
        path = os.path.abspath(filename)

    if os.path.isfile(path):
        with open(path) as projects_fh:
            projects_dict = yaml.safe_load(projects_fh)
            return projects_dict
    else:
        msg = 'Unable to load projects file at %s' % path
        raise Exception(msg)


def logged_sleep(duration, level='DEBUG', stack_depth=1):
    level = getattr(logging, level.upper())
    # based on
    # http://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
    try:
        frm = inspect.stack()[stack_depth]
        logger = logging.getLogger(inspect.getmodule(frm[0]).__name__)
    except AttributeError:  # module is None (interactive shell)
        logger = log  # fall back to utils logger
    logger.log(level, 'Sleeping for {0} seconds.'.format(duration))
    time.sleep(duration)


def poll_until(function, interval=5, timeout=0):
    """Polls `function` every `interval` seconds until it returns a non-falsey
    value. If this does not occur within the provided `timeout`,
    a WaitUntilTimeout is raised.

    Each attempt will log the time that has elapsed since the original
    request.
    """
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        log.debug('elapsed: {0:4.1f}'.format(elapsed))

        value = function()
        if value:
            return value

        if elapsed > timeout:
            break

        logged_sleep(interval, stack_depth=3)

    msg = 'Timeout after {0} seconds.'.format(elapsed)
    raise WaitUntilTimeout(None, msg)


def gen_utf_char():
    is_char = False
    b = 'b'
    while not is_char:
        b = random.randint(32, 0x10FFFF)
        is_char = chr(b).isprintable()
    return chr(b)


def random_int(maxint=sys.maxsize):
    max = int(maxint)
    return random.randint(0, max)


def random_ipv4():
    """Generates a random ipv4 address;; useful for testing."""
    return ".".join(str(random.randint(1, 255)) for i in range(4))


def random_ipv6():
    """Generates a random ipv6 address;; useful for testing."""
    return ':'.join('{0:x}'.format(random.randint(0, 2**16 - 1)) for i in range(8))


def random_loopback_ip():
    """Generates a random loopback ipv4 address;; useful for testing."""
    return "127.{}.{}.{}".format(random_int(255), random_int(255), random_int(255))


def random_utf8(*args, **kwargs):
    """This function exists due to a bug in ChromeDriver that throws an
    exception when a character outside of the BMP is sent to `send_keys`.
    Code pulled from http://stackoverflow.com/a/3220210.
    """
    pattern = re.compile('[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    length = args[0] if len(args) else kwargs.get('length', 10)
    scrubbed = pattern.sub('\uFFFD', ''.join([gen_utf_char() for _ in range(length)]))

    return scrubbed


def random_title(num_words=2, non_ascii=True):
    base = ''.join([random.choice(words) for word in range(num_words)])
    if os.getenv('AWXKIT_FORCE_ONLY_ASCII', False):
        title = ''.join([base, ''.join(str(random_int(99)))])
    else:
        if non_ascii:
            title = ''.join([base, random_utf8(1)])
        else:
            title = ''.join([base, ''.join([str(random_int()) for _ in range(3)])])
    return title


def update_payload(payload, fields, kwargs):
    """Takes a list of fields and adds their kwargs value to payload if defined.
    If the payload has an existing value and not_provided is the kwarg value for that key,
    the existing key/value are stripped from the payload.
    """
    not_provided_as_kwarg = 'xx_UPDATE_PAYLOAD_FIELD_NOT_PROVIDED_AS_KWARG_xx'
    for field in fields:
        field_val = kwargs.get(field, not_provided_as_kwarg)
        if field_val not in (not_provided, not_provided_as_kwarg):
            payload[field] = field_val
        elif field in payload and field_val == not_provided:
            payload.pop(field)
    return payload


def set_payload_foreign_key_args(payload, fk_fields, kwargs):
    if isinstance(fk_fields, str):
        fk_fields = (fk_fields,)

    for fk_field in fk_fields:
        rel_obj = kwargs.get(fk_field)
        if rel_obj is None:
            continue
        elif isinstance(rel_obj, int):
            payload.update(**{fk_field: int(rel_obj)})
        elif hasattr(rel_obj, 'id'):
            payload.update(**{fk_field: rel_obj.id})
        else:
            raise AttributeError(f'Related field {fk_field} must be either integer of pkid or object')
    return payload


def to_str(obj):
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    return obj


def to_bool(obj):
    if isinstance(obj, (str,)):
        return obj.lower() not in ('false', 'off', 'no', 'n', '0', '')
    return bool(obj)


def load_json_or_yaml(obj):
    try:
        return yaml.safe_load(obj)
    except AttributeError:
        raise TypeError("Provide valid YAML/JSON.")


def get_class_if_instance(obj):
    if not inspect.isclass(obj):
        return obj.__class__
    return obj


def class_name_to_kw_arg(class_name):
    """'ClassName' -> 'class_name'"""
    first_pass = re.sub(r'([a-z])([A-Z0-9])', r'\1_\2', class_name)
    second_pass = re.sub(r'([0-9])([a-zA-Z])', r'\1_\2', first_pass).lower()
    return second_pass.replace('v2_', '')


def is_proper_subclass(obj, cls):
    return inspect.isclass(obj) and obj is not cls and issubclass(obj, cls)


def are_same_endpoint(first, second):
    """Equivalence check of two urls, stripped of query parameters"""

    def strip(url):
        return url.replace('www.', '').split('?')[0]

    return strip(first) == strip(second)


def utcnow():
    """Provide a wrapped copy of the built-in utcnow that can be easily mocked."""
    return datetime.utcnow()


class UTC(tzinfo):
    """Concrete implementation of tzinfo for UTC. For more information, see:
    https://docs.python.org/2/library/datetime.html
    """

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return timedelta(0)

    def utcoffset(self, dt):
        return timedelta(0)


def seconds_since_date_string(date_str, fmt='%Y-%m-%dT%H:%M:%S.%fZ', default_tz=UTC()):
    """Return the number of seconds since the date and time indicated by a date
    string and its corresponding format string.

    :param date_str: string representing a date and time.
    :param fmt: Formatting string - by default, this value is set to parse
        date strings originating from awx API response data.
    :param default_tz: Assumed tzinfo if the parsed date_str does not include tzinfo

    For more information on python date string formatting directives, see
        https://docs.python.org/2/library/datetime.httpsml#strftime-strptime-behavior
    """
    parsed_datetime = datetime.strptime(date_str, fmt)

    if not parsed_datetime.tzinfo:
        parsed_datetime = parsed_datetime.replace(tzinfo=default_tz)

    elapsed = utcnow().replace(tzinfo=UTC()) - parsed_datetime

    return elapsed.total_seconds()


def to_ical(dt):
    return re.sub('[:-]', '', dt.strftime("%Y%m%dT%H%M%SZ"))


def version_from_endpoint(endpoint):
    return endpoint.split('/api/')[1].split('/')[0] or 'common'


def args_string_to_list(args):
    """Converts cmdline arg string to list of args.  The reverse of subprocess.list2cmdline()
    heavily inspired by robot.utils.argumentparser.cmdline2list()
    """
    lexer = shlex.shlex(args, posix=True)
    lexer.escapedquotes = '"\''
    lexer.commenters = ''
    lexer.whitespace_split = True
    return [token.decode('utf-8') for token in lexer]


def is_list_or_tuple(item):
    return isinstance(item, list) or isinstance(item, tuple)
