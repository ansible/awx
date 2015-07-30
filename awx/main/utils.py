# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import base64
import hashlib
import logging
import os
import re
import subprocess
import stat
import sys
import urllib
import urlparse
import threading
import contextlib
import tempfile

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse

# PyCrypto
from Crypto.Cipher import AES

logger = logging.getLogger('awx.main.utils')

__all__ = ['get_object_or_400', 'get_object_or_403', 'camelcase_to_underscore',
           'get_ansible_version', 'get_ssh_version', 'get_awx_version', 'update_scm_url',
           'get_type_for_model', 'get_model_for_type', 'to_python_boolean',
           'ignore_inventory_computed_fields', 'ignore_inventory_group_removal',
           '_inventory_updates', 'get_pk_from_dict']


def get_object_or_400(klass, *args, **kwargs):
    '''
    Return a single object from the given model or queryset based on the query
    params, otherwise raise an exception that will return in a 400 response.
    '''
    from django.shortcuts import _get_queryset
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist, e:
        raise ParseError(*e.args)
    except queryset.model.MultipleObjectsReturned, e:
        raise ParseError(*e.args)


def get_object_or_403(klass, *args, **kwargs):
    '''
    Return a single object from the given model or queryset based on the query
    params, otherwise raise an exception that will return in a 403 response.
    '''
    from django.shortcuts import _get_queryset
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist, e:
        raise PermissionDenied(*e.args)
    except queryset.model.MultipleObjectsReturned, e:
        raise PermissionDenied(*e.args)

def to_python_boolean(value, allow_none=False):
    value = unicode(value)
    if value.lower() in ('true', '1', 't'):
        return True
    elif value.lower() in ('false', '0', 'f'):
        return False
    elif allow_none and value.lower() in ('none', 'null'):
        return None
    else:
        raise ValueError(u'Unable to convert "%s" to boolean' % unicode(value))

def camelcase_to_underscore(s):
    '''
    Convert CamelCase names to lowercase_with_underscore.
    '''
    s = re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s)
    return s.lower().strip('_')


class RequireDebugTrueOrTest(logging.Filter):
    '''
    Logging filter to output when in DEBUG mode or running tests.
    '''

    def filter(self, record):
        from django.conf import settings
        return settings.DEBUG or 'test' in sys.argv


def get_ansible_version():
    '''
    Return Ansible version installed.
    '''
    try:
        proc = subprocess.Popen(['ansible', '--version'],
                                stdout=subprocess.PIPE)
        result = proc.communicate()[0]
        stripped_result = result.split('\n')[0].replace('ansible', '').strip()
        return stripped_result
    except:
        return 'unknown'

def get_ssh_version():
    '''
    Return SSH version installed.
    '''
    try:
        proc = subprocess.Popen(['ssh', '-V'],
                                stderr=subprocess.PIPE)
        result = proc.communicate()[1]
        return result.split(" ")[0].split("_")[1]
    except:
        return 'unknown'

def get_awx_version():
    '''
    Return Ansible Tower version as reported by setuptools.
    '''
    from awx import __version__
    try:
        import pkg_resources
        return pkg_resources.require('ansible_tower')[0].version
    except:
        return __version__


def get_encryption_key(instance, field_name):
    '''
    Generate key for encrypted password based on instance pk and field name.
    '''
    from django.conf import settings
    h = hashlib.sha1()
    h.update(settings.SECRET_KEY)
    h.update(str(instance.pk))
    h.update(field_name)
    return h.digest()[:16]


def encrypt_field(instance, field_name, ask=False):
    '''
    Return content of the given instance and field name encrypted.
    '''
    value = getattr(instance, field_name)
    if not value or value.startswith('$encrypted$') or (ask and value == 'ASK'):
        return value
    value = value.encode('utf-8')
    key = get_encryption_key(instance, field_name)
    cipher = AES.new(key, AES.MODE_ECB)
    while len(value) % cipher.block_size != 0:
        value += '\x00'
    encrypted = cipher.encrypt(value)
    b64data = base64.b64encode(encrypted)
    return '$encrypted$%s$%s' % ('AES', b64data)


def decrypt_field(instance, field_name):
    '''
    Return content of the given instance and field name decrypted.
    '''
    value = getattr(instance, field_name)
    if not value or not value.startswith('$encrypted$'):
        return value
    algo, b64data = value[len('$encrypted$'):].split('$', 1)
    if algo != 'AES':
        raise ValueError('unsupported algorithm: %s' % algo)
    encrypted = base64.b64decode(b64data)
    key = get_encryption_key(instance, field_name)
    cipher = AES.new(key, AES.MODE_ECB)
    value = cipher.decrypt(encrypted)
    return value.rstrip('\x00')


def update_scm_url(scm_type, url, username=True, password=True,
                   check_special_cases=True, scp_format=False):
    '''
    Update the given SCM URL to add/replace/remove the username/password. When
    username/password is True, preserve existing username/password, when
    False (None, '', etc.), remove any existing username/password, otherwise
    replace username/password. Also validates the given URL.
    '''
    # Handle all of the URL formats supported by the SCM systems:
    # git: https://www.kernel.org/pub/software/scm/git/docs/git-clone.html#URLS
    # hg: http://www.selenic.com/mercurial/hg.1.html#url-paths
    # svn: http://svnbook.red-bean.com/en/1.7/svn-book.html#svn.advanced.reposurls
    if scm_type not in ('git', 'hg', 'svn'):
        raise ValueError('Unsupported SCM type "%s"' % str(scm_type))
    if not url.strip():
        return ''
    parts = urlparse.urlsplit(url)
    try:
        parts.port
    except ValueError:
        raise ValueError('Invalid %s URL' % scm_type)
    if parts.scheme == 'git+ssh' and not scp_format:
        raise ValueError('Unsupported %s URL' % scm_type)

    if '://' not in url:
        # Handle SCP-style URLs for git (e.g. [user@]host.xz:path/to/repo.git/).
        if scm_type == 'git' and ':' in url:
            if '@' in url:
                userpass, hostpath = url.split('@', 1)
            else:
                userpass, hostpath = '', url
            if hostpath.count(':') > 1:
                raise ValueError('Invalid %s URL' % scm_type)
            host, path = hostpath.split(':', 1)
            #if not path.startswith('/') and not path.startswith('~/'):
            #    path = '~/%s' % path
            #if path.startswith('/'):
            #    path = path.lstrip('/')
            hostpath = '/'.join([host, path])
            modified_url = '@'.join(filter(None, [userpass, hostpath]))
            # git+ssh scheme identifies URLs that should be converted back to
            # SCP style before passed to git module.
            parts = urlparse.urlsplit('git+ssh://%s' % modified_url)
        # Handle local paths specified without file scheme (e.g. /path/to/foo).
        # Only supported by git and hg. (not currently allowed)
        elif scm_type in ('git', 'hg'):
            if not url.startswith('/'):
                parts = urlparse.urlsplit('file:///%s' % url)
            else:
                parts = urlparse.urlsplit('file://%s' % url)
        else:
            raise ValueError('Invalid %s URL' % scm_type)

    # Validate that scheme is valid for given scm_type.
    scm_type_schemes = {
        'git': ('ssh', 'git', 'git+ssh', 'http', 'https', 'ftp', 'ftps'),
        'hg': ('http', 'https', 'ssh'),
        'svn': ('http', 'https', 'svn', 'svn+ssh'),
    }
    if parts.scheme not in scm_type_schemes.get(scm_type, ()):
        raise ValueError('Unsupported %s URL' % scm_type)
    if parts.scheme == 'file' and parts.netloc not in ('', 'localhost'):
        raise ValueError('Unsupported host "%s" for file:// URL' % (parts.netloc))
    elif parts.scheme != 'file' and not parts.netloc:
        raise ValueError('Host is required for %s URL' % parts.scheme)
    if username is True:
        netloc_username = parts.username or ''
    elif username:
        netloc_username = username
    else:
        netloc_username = ''
    if password is True:
        netloc_password = parts.password or ''
    elif password:
        netloc_password = password
    else:
        netloc_password = ''

    # Special handling for github/bitbucket SSH URLs.
    if check_special_cases:
        special_git_hosts = ('github.com', 'bitbucket.org', 'altssh.bitbucket.org')
        if scm_type == 'git' and parts.scheme.endswith('ssh') and parts.hostname in special_git_hosts and netloc_username != 'git':
            raise ValueError('Username must be "git" for SSH access to %s.' % parts.hostname)
        if scm_type == 'git' and parts.scheme.endswith('ssh') and parts.hostname in special_git_hosts and netloc_password:
            #raise ValueError('Password not allowed for SSH access to %s.' % parts.hostname)
            netloc_password = ''
        special_hg_hosts = ('bitbucket.org', 'altssh.bitbucket.org')
        if scm_type == 'hg' and parts.scheme == 'ssh' and parts.hostname in special_hg_hosts and netloc_username != 'hg':
            raise ValueError('Username must be "hg" for SSH access to %s.' % parts.hostname)
        if scm_type == 'hg' and parts.scheme == 'ssh' and netloc_password:
            #raise ValueError('Password not supported for SSH with Mercurial.')
            netloc_password = ''

    if netloc_username and parts.scheme != 'file':
        netloc = u':'.join([urllib.quote(x) for x in (netloc_username, netloc_password) if x])
    else:
        netloc = u''
    netloc = u'@'.join(filter(None, [netloc, parts.hostname]))
    if parts.port:
        netloc = u':'.join([netloc, unicode(parts.port)])
    new_url = urlparse.urlunsplit([parts.scheme, netloc, parts.path,
                                   parts.query, parts.fragment])
    if scp_format and parts.scheme == 'git+ssh':
        new_url = new_url.replace('git+ssh://', '', 1).replace('/', ':', 1)
    return new_url


def model_instance_diff(old, new, serializer_mapping=None):
    """
    Calculate the differences between two model instances. One of the instances may be None (i.e., a newly
    created model or deleted model). This will cause all fields with a value to have changed (from None).
    serializer_mapping are used to determine read-only fields.
    When provided, read-only fields will not be included in the resulting dictionary
    """
    from django.db.models import Model
    from awx.main.models.credential import Credential

    if not(old is None or isinstance(old, Model)):
        raise TypeError('The supplied old instance is not a valid model instance.')
    if not(new is None or isinstance(new, Model)):
        raise TypeError('The supplied new instance is not a valid model instance.')

    diff = {}

    if serializer_mapping is not None and new.__class__ in serializer_mapping:
        serializer_actual = serializer_mapping[new.__class__]()
        allowed_fields = [x for x in serializer_actual.fields if not serializer_actual.fields[x].read_only] + ['id']
    else:
        allowed_fields = [x.name for x in new._meta.fields]

    for field in allowed_fields:
        old_value = getattr(old, field, None)
        new_value = getattr(new, field, None)

        if old_value != new_value and field not in Credential.PASSWORD_FIELDS:
            if type(old_value) not in (bool, int, type(None)):
                old_value = smart_str(old_value)
            if type(new_value) not in (bool, int, type(None)):
                new_value = smart_str(new_value)
            diff[field] = (old_value, new_value)
        elif old_value != new_value and field in Credential.PASSWORD_FIELDS:
            diff[field] = (u"hidden", u"hidden")

    if len(diff) == 0:
        diff = None

    return diff


def model_to_dict(obj, serializer_mapping=None):
    """
    Serialize a model instance to a dictionary as best as possible
    serializer_mapping are used to determine read-only fields.
    When provided, read-only fields will not be included in the resulting dictionary
    """
    from awx.main.models.credential import Credential
    attr_d = {}
    if serializer_mapping is not None and obj.__class__ in serializer_mapping:
        serializer_actual = serializer_mapping[obj.__class__]()
        allowed_fields = [x for x in serializer_actual.fields if not serializer_actual.fields[x].read_only] + ['id']
    else:
        allowed_fields = [x.name for x in obj._meta.fields]
    for field in obj._meta.fields:
        if field.name not in allowed_fields:
            continue
        if field.name not in Credential.PASSWORD_FIELDS:
            field_val = getattr(obj, field.name, None)
            if type(field_val) not in (bool, int, type(None)):
                attr_d[field.name] = smart_str(field_val)
            else:
                attr_d[field.name] = field_val
        else:
            attr_d[field.name] = "hidden"
    return attr_d


def get_type_for_model(model):
    '''
    Return type name for a given model class.
    '''
    from rest_framework.compat import get_concrete_model
    opts = get_concrete_model(model)._meta
    return camelcase_to_underscore(opts.object_name)


def get_model_for_type(type):
    '''
    Return model class for a given type name.
    '''
    from django.db.models import Q
    from django.contrib.contenttypes.models import ContentType
    for ct in ContentType.objects.filter(Q(app_label='main') | Q(app_label='auth', model='user')):
        ct_model = ct.model_class()
        if not ct_model:
            continue
        ct_type = get_type_for_model(ct_model)
        if type == ct_type:
            return ct_model


def get_system_task_capacity():
    '''
    Measure system memory and use it as a baseline for determining the system's capacity
    '''
    from django.conf import settings
    if hasattr(settings, 'SYSTEM_TASK_CAPACITY'):
        return settings.SYSTEM_TASK_CAPACITY
    proc = subprocess.Popen(['free', '-m'], stdout=subprocess.PIPE)
    out,err = proc.communicate()
    total_mem_value = out.split()[7]
    if int(total_mem_value) <= 2048:
        return 50
    return 50 + ((int(total_mem_value) / 1024) - 2) * 75


def emit_websocket_notification(endpoint, event, payload):
    from awx.main.socket import Socket

    try:
        with Socket('websocket', 'w', nowait=True, logger=logger) as websocket:
            payload['event'] = event
            payload['endpoint'] = endpoint
            websocket.publish(payload)
    except Exception:
        pass

_inventory_updates = threading.local()


@contextlib.contextmanager
def ignore_inventory_computed_fields():
    '''
    Context manager to ignore updating inventory computed fields.
    '''
    try:
        previous_value = getattr(_inventory_updates, 'is_updating', False)
        _inventory_updates.is_updating = True
        yield
    finally:
        _inventory_updates.is_updating = previous_value


@contextlib.contextmanager
def ignore_inventory_group_removal():
    '''
    Context manager to ignore moving groups/hosts when group is deleted.
    '''
    try:
        previous_value = getattr(_inventory_updates, 'is_removing', False)
        _inventory_updates.is_removing = True
        yield
    finally:
        _inventory_updates.is_removing = previous_value

def check_proot_installed():
    '''
    Check that proot is installed.
    '''
    from django.conf import settings
    cmd = [getattr(settings, 'AWX_PROOT_CMD', 'proot'), '--version']
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.communicate()
        return bool(proc.returncode == 0)
    except (OSError, ValueError):
        return False

def build_proot_temp_dir():
    '''
    Create a temporary directory for proot to use.
    '''
    path = tempfile.mkdtemp(prefix='ansible_tower_proot_')
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return path

def wrap_args_with_proot(args, cwd, **kwargs):
    '''
    Wrap existing command line with proot to restrict access to:
     - /etc/tower (to prevent obtaining db info or secret key)
     - /var/lib/awx (except for current project)
     - /var/log/tower
     - /var/log/supervisor
     - /tmp (except for own tmp files)
    '''
    from django.conf import settings
    new_args = [getattr(settings, 'AWX_PROOT_CMD', 'proot'), '-v',
                str(getattr(settings, 'AWX_PROOT_VERBOSITY', '0')), '-r', '/']
    hide_paths = ['/etc/tower', '/var/lib/awx', '/var/log',
                  tempfile.gettempdir(), settings.PROJECTS_ROOT,
                  settings.JOBOUTPUT_ROOT]
    hide_paths.extend(getattr(settings, 'AWX_PROOT_HIDE_PATHS', None) or [])
    for path in sorted(set(hide_paths)):
        if not os.path.exists(path):
            continue
        if os.path.isdir(path):
            new_path = tempfile.mkdtemp(dir=kwargs['proot_temp_dir'])
            os.chmod(new_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        else:
            handle, new_path = tempfile.mkstemp(dir=kwargs['proot_temp_dir'])
            os.close(handle)
            os.chmod(new_path, stat.S_IRUSR | stat.S_IWUSR)
        new_args.extend(['-b', '%s:%s' % (new_path, path)])
    if 'private_data_dir' in kwargs:
        show_paths = [cwd, kwargs['private_data_dir']]
    else:
        show_paths = [cwd]
    show_paths.extend(getattr(settings, 'AWX_PROOT_SHOW_PATHS', None) or [])
    for path in sorted(set(show_paths)):
        if not os.path.exists(path):
            continue
        new_args.extend(['-b', '%s:%s' % (path, path)])
    new_args.extend(['-w', cwd])
    new_args.extend(args)
    return new_args

def get_pk_from_dict(_dict, key):
    '''
    Helper for obtaining a pk from user data dict or None if not present.
    '''
    try:
        return int(_dict[key])
    except (TypeError, KeyError, ValueError):
        return None

def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.urlencode(get)
    return url

def timestamp_apiformat(timestamp):
    timestamp = timestamp.isoformat()
    if timestamp.endswith('+00:00'):
        timestamp = timestamp[:-6] + 'Z'
    return timestamp

# damn you python 2.6
def timedelta_total_seconds(timedelta):
    return (
        timedelta.microseconds + 0.0 +
        (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6


