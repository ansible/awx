# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import base64
import json
import yaml
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
import six
import psutil

# Decorator
from decorator import decorator

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied
from django.utils.encoding import smart_str
from django.utils.text import slugify
from django.apps import apps

logger = logging.getLogger('awx.main.utils')

__all__ = ['get_object_or_400', 'get_object_or_403', 'camelcase_to_underscore', 'memoize', 'memoize_delete',
           'get_ansible_version', 'get_ssh_version', 'get_licenser', 'get_awx_version', 'update_scm_url',
           'get_type_for_model', 'get_model_for_type', 'copy_model_by_class',
           'copy_m2m_relationships' ,'cache_list_capabilities', 'to_python_boolean',
           'ignore_inventory_computed_fields', 'ignore_inventory_group_removal',
           '_inventory_updates', 'get_pk_from_dict', 'getattrd', 'NoDefaultProvided',
           'get_current_apps', 'set_current_apps', 'OutputEventFilter',
           'callback_filter_out_ansible_extra_vars', 'get_search_fields', 'get_system_task_capacity',
           'wrap_args_with_proot', 'build_proot_temp_dir', 'check_proot_installed', 'model_to_dict',
           'model_instance_diff', 'timestamp_apiformat', 'parse_yaml_or_json', 'RequireDebugTrueOrTest',
           'has_model_field_prefetched', 'set_environ', 'IllegalArgumentError',]


def get_object_or_400(klass, *args, **kwargs):
    '''
    Return a single object from the given model or queryset based on the query
    params, otherwise raise an exception that will return in a 400 response.
    '''
    from django.shortcuts import _get_queryset
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist as e:
        raise ParseError(*e.args)
    except queryset.model.MultipleObjectsReturned as e:
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
    except queryset.model.DoesNotExist as e:
        raise PermissionDenied(*e.args)
    except queryset.model.MultipleObjectsReturned as e:
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
        raise ValueError(_(u'Unable to convert "%s" to boolean') % unicode(value))


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


class IllegalArgumentError(ValueError):
    pass


def memoize(ttl=60, cache_key=None, track_function=False):
    '''
    Decorator to wrap a function and cache its result.
    '''
    from django.core.cache import cache


    def _memoizer(f, *args, **kwargs):
        if cache_key and track_function:
            raise IllegalArgumentError("Can not specify cache_key when track_function is True")

        if track_function:
            cache_dict_key = slugify('%r %r' % (args, kwargs))
            key = slugify("%s" % f.__name__)
            cache_dict = cache.get(key) or dict()
            if cache_dict_key not in cache_dict:
                value = f(*args, **kwargs)
                cache_dict[cache_dict_key] = value
                cache.set(key, cache_dict, ttl)
            else:
                value = cache_dict[cache_dict_key]
        else:
            key = cache_key or slugify('%s %r %r' % (f.__name__, args, kwargs))
            value = cache.get(key)
            if value is None:
                value = f(*args, **kwargs)
                cache.set(key, value, ttl)

        return value
    return decorator(_memoizer)


def memoize_delete(function_name):
    from django.core.cache import cache

    return cache.delete(function_name)


@memoize()
def get_ansible_version():
    '''
    Return Ansible version installed.
    '''
    try:
        proc = subprocess.Popen(['ansible', '--version'],
                                stdout=subprocess.PIPE)
        result = proc.communicate()[0]
        return result.split('\n')[0].replace('ansible', '').strip()
    except:
        return 'unknown'


@memoize()
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
    Return AWX version as reported by setuptools.
    '''
    from awx import __version__
    try:
        import pkg_resources
        return pkg_resources.require('awx')[0].version
    except:
        return __version__


class StubLicense(object):

    features = {
        'activity_streams': True,
        'ha': True,
        'ldap': True,
        'multiple_organizations': True,
        'surveys': True,
        'system_tracking': True,
        'rebranding': True,
        'enterprise_auth': True,
        'workflows': True,
    }

    def validate(self):
        return dict(license_key='OPEN',
                    valid_key=True,
                    compliant=True,
                    features=self.features,
                    license_type='open')


def get_licenser(*args, **kwargs):
    try:
        from tower_license import TowerLicense
        return TowerLicense(*args, **kwargs)
    except ImportError:
        return StubLicense(*args, **kwargs)


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
    if scm_type not in ('git', 'hg', 'svn', 'insights'):
        raise ValueError(_('Unsupported SCM type "%s"') % str(scm_type))
    if not url.strip():
        return ''
    parts = urlparse.urlsplit(url)
    try:
        parts.port
    except ValueError:
        raise ValueError(_('Invalid %s URL') % scm_type)
    if parts.scheme == 'git+ssh' and not scp_format:
        raise ValueError(_('Unsupported %s URL') % scm_type)

    if '://' not in url:
        # Handle SCP-style URLs for git (e.g. [user@]host.xz:path/to/repo.git/).
        if scm_type == 'git' and ':' in url:
            if '@' in url:
                userpass, hostpath = url.split('@', 1)
            else:
                userpass, hostpath = '', url
            if hostpath.count(':') > 1:
                raise ValueError(_('Invalid %s URL') % scm_type)
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
        # Only supported by git and hg.
        elif scm_type in ('git', 'hg'):
            if not url.startswith('/'):
                parts = urlparse.urlsplit('file:///%s' % url)
            else:
                parts = urlparse.urlsplit('file://%s' % url)
        else:
            raise ValueError(_('Invalid %s URL') % scm_type)

    # Validate that scheme is valid for given scm_type.
    scm_type_schemes = {
        'git': ('ssh', 'git', 'git+ssh', 'http', 'https', 'ftp', 'ftps', 'file'),
        'hg': ('http', 'https', 'ssh', 'file'),
        'svn': ('http', 'https', 'svn', 'svn+ssh', 'file'),
        'insights': ('http', 'https')
    }
    if parts.scheme not in scm_type_schemes.get(scm_type, ()):
        raise ValueError(_('Unsupported %s URL') % scm_type)
    if parts.scheme == 'file' and parts.netloc not in ('', 'localhost'):
        raise ValueError(_('Unsupported host "%s" for file:// URL') % (parts.netloc))
    elif parts.scheme != 'file' and not parts.netloc:
        raise ValueError(_('Host is required for %s URL') % parts.scheme)
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
            raise ValueError(_('Username must be "git" for SSH access to %s.') % parts.hostname)
        if scm_type == 'git' and parts.scheme.endswith('ssh') and parts.hostname in special_git_hosts and netloc_password:
            #raise ValueError('Password not allowed for SSH access to %s.' % parts.hostname)
            netloc_password = ''
        special_hg_hosts = ('bitbucket.org', 'altssh.bitbucket.org')
        if scm_type == 'hg' and parts.scheme == 'ssh' and parts.hostname in special_hg_hosts and netloc_username != 'hg':
            raise ValueError(_('Username must be "hg" for SSH access to %s.') % parts.hostname)
        if scm_type == 'hg' and parts.scheme == 'ssh' and netloc_password:
            #raise ValueError('Password not supported for SSH with Mercurial.')
            netloc_password = ''

    if netloc_username and parts.scheme != 'file' and scm_type != "insights":
        netloc = u':'.join([urllib.quote(x,safe='') for x in (netloc_username, netloc_password) if x])
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


def get_allowed_fields(obj, serializer_mapping):
    from django.contrib.auth.models import User

    if serializer_mapping is not None and obj.__class__ in serializer_mapping:
        serializer_actual = serializer_mapping[obj.__class__]()
        allowed_fields = [x for x in serializer_actual.fields if not serializer_actual.fields[x].read_only] + ['id']
    else:
        allowed_fields = [x.name for x in obj._meta.fields]

    if isinstance(obj, User):
        field_blacklist = ['last_login']
        allowed_fields = [f for f in allowed_fields if f not in field_blacklist]

    return allowed_fields


def _convert_model_field_for_display(obj, field_name, password_fields=None):
    # NOTE: Careful modifying the value of field_val, as it could modify
    # underlying model object field value also.
    try:
        field_val = getattr(obj, field_name, None)
    except ObjectDoesNotExist:
        return '<missing {}>-{}'.format(obj._meta.verbose_name, getattr(obj, '{}_id'.format(field_name)))
    if password_fields is None:
        password_fields = set(getattr(type(obj), 'PASSWORD_FIELDS', [])) | set(['password'])
    if field_name in password_fields or (
        isinstance(field_val, six.string_types) and
        field_val.startswith('$encrypted$')
    ):
        return u'hidden'
    if hasattr(obj, 'display_%s' % field_name):
        field_val = getattr(obj, 'display_%s' % field_name)()
    if isinstance(field_val, (list, dict)):
        try:
            field_val = json.dumps(field_val, ensure_ascii=False)
        except Exception:
            pass
    if type(field_val) not in (bool, int, type(None)):
        field_val = smart_str(field_val)
    return field_val


def model_instance_diff(old, new, serializer_mapping=None):
    """
    Calculate the differences between two model instances. One of the instances may be None (i.e., a newly
    created model or deleted model). This will cause all fields with a value to have changed (from None).
    serializer_mapping are used to determine read-only fields.
    When provided, read-only fields will not be included in the resulting dictionary
    """
    from django.db.models import Model

    if not(old is None or isinstance(old, Model)):
        raise TypeError('The supplied old instance is not a valid model instance.')
    if not(new is None or isinstance(new, Model)):
        raise TypeError('The supplied new instance is not a valid model instance.')
    old_password_fields = set(getattr(type(old), 'PASSWORD_FIELDS', [])) | set(['password'])
    new_password_fields = set(getattr(type(new), 'PASSWORD_FIELDS', [])) | set(['password'])

    diff = {}

    allowed_fields = get_allowed_fields(new, serializer_mapping)

    for field in allowed_fields:
        old_value = getattr(old, field, None)
        new_value = getattr(new, field, None)
        if old_value != new_value:
            diff[field] = (
                _convert_model_field_for_display(old, field, password_fields=old_password_fields),
                _convert_model_field_for_display(new, field, password_fields=new_password_fields),
            )

    if len(diff) == 0:
        diff = None

    return diff


def model_to_dict(obj, serializer_mapping=None):
    """
    Serialize a model instance to a dictionary as best as possible
    serializer_mapping are used to determine read-only fields.
    When provided, read-only fields will not be included in the resulting dictionary
    """
    password_fields = set(getattr(type(obj), 'PASSWORD_FIELDS', [])) | set(['password'])
    attr_d = {}

    allowed_fields = get_allowed_fields(obj, serializer_mapping)

    for field in obj._meta.fields:
        if field.name not in allowed_fields:
            continue
        attr_d[field.name] = _convert_model_field_for_display(obj, field.name, password_fields=password_fields)

    return attr_d


def copy_model_by_class(obj1, Class2, fields, kwargs):
    '''
    Creates a new unsaved object of type Class2 using the fields from obj1
    values in kwargs can override obj1
    '''
    create_kwargs = {}
    for field_name in fields:
        # Foreign keys can be specified as field_name or field_name_id.
        id_field_name = '%s_id' % field_name
        if hasattr(obj1, id_field_name):
            if field_name in kwargs:
                value = kwargs[field_name]
            elif id_field_name in kwargs:
                value = kwargs[id_field_name]
            else:
                value = getattr(obj1, id_field_name)
            if hasattr(value, 'id'):
                value = value.id
            create_kwargs[id_field_name] = value
        elif field_name in kwargs:
            if field_name == 'extra_vars' and isinstance(kwargs[field_name], dict):
                create_kwargs[field_name] = json.dumps(kwargs['extra_vars'])
            elif not isinstance(Class2._meta.get_field(field_name), (ForeignObjectRel, ManyToManyField)):
                create_kwargs[field_name] = kwargs[field_name]
        elif hasattr(obj1, field_name):
            field_obj = obj1._meta.get_field_by_name(field_name)[0]
            if not isinstance(field_obj, ManyToManyField):
                create_kwargs[field_name] = getattr(obj1, field_name)

    # Apply class-specific extra processing for origination of unified jobs
    if hasattr(obj1, '_update_unified_job_kwargs') and obj1.__class__ != Class2:
        new_kwargs = obj1._update_unified_job_kwargs(create_kwargs, kwargs)
    else:
        new_kwargs = create_kwargs

    return Class2(**new_kwargs)


def copy_m2m_relationships(obj1, obj2, fields, kwargs=None):
    '''
    In-place operation.
    Given two saved objects, copies related objects from obj1
    to obj2 to field of same name, if field occurs in `fields`
    '''
    for field_name in fields:
        if hasattr(obj1, field_name):
            field_obj = obj1._meta.get_field_by_name(field_name)[0]
            if isinstance(field_obj, ManyToManyField):
                # Many to Many can be specified as field_name
                src_field_value = getattr(obj1, field_name)
                if kwargs and field_name in kwargs:
                    override_field_val = kwargs[field_name]
                    if isinstance(override_field_val, list):
                        getattr(obj2, field_name).add(*override_field_val)
                        continue
                    if override_field_val.__class__.__name__ is 'ManyRelatedManager':
                        src_field_value = override_field_val
                dest_field = getattr(obj2, field_name)
                dest_field.add(*list(src_field_value.all().values_list('id', flat=True)))


def get_type_for_model(model):
    '''
    Return type name for a given model class.
    '''
    opts = model._meta.concrete_model._meta
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


def cache_list_capabilities(page, prefetch_list, model, user):
    '''
    Given a `page` list of objects, the specified roles for the specified user
    are save on each object in the list, using 1 query for each role type

    Examples:
    capabilities_prefetch = ['admin', 'execute']
      --> prefetch the admin (edit) and execute (start) permissions for
          items in list for current user
    capabilities_prefetch = ['inventory.admin']
      --> prefetch the related inventory FK permissions for current user,
          and put it into the object's cache
    capabilities_prefetch = [{'copy': ['inventory.admin', 'project.admin']}]
      --> prefetch logical combination of admin permission to inventory AND
          project, put into cache dictionary as "copy"
    '''
    from django.db.models import Q
    page_ids = [obj.id for obj in page]
    for obj in page:
        obj.capabilities_cache = {}

    skip_models = []
    if hasattr(model, 'invalid_user_capabilities_prefetch_models'):
        skip_models = model.invalid_user_capabilities_prefetch_models()

    for prefetch_entry in prefetch_list:

        display_method = None
        if type(prefetch_entry) is dict:
            display_method = prefetch_entry.keys()[0]
            paths = prefetch_entry[display_method]
        else:
            paths = prefetch_entry

        if type(paths) is not list:
            paths = [paths]

        # Build the query for accessible_objects according the user & role(s)
        filter_args = []
        for role_path in paths:
            if '.' in role_path:
                res_path = '__'.join(role_path.split('.')[:-1])
                role_type = role_path.split('.')[-1]
                parent_model = model
                for subpath in role_path.split('.')[:-1]:
                    parent_model = parent_model._meta.get_field(subpath).related_model
                filter_args.append(Q(
                    Q(**{'%s__pk__in' % res_path: parent_model.accessible_pk_qs(user, '%s_role' % role_type)}) |
                    Q(**{'%s__isnull' % res_path: True})))
            else:
                role_type = role_path
                filter_args.append(Q(**{'pk__in': model.accessible_pk_qs(user, '%s_role' % role_type)}))

        if display_method is None:
            # Role name translation to UI names for methods
            display_method = role_type
            if role_type == 'admin':
                display_method = 'edit'
            elif role_type in ['execute', 'update']:
                display_method = 'start'

        # Union that query with the list of items on page
        filter_args.append(Q(pk__in=page_ids))
        ids_with_role = set(model.objects.filter(*filter_args).values_list('pk', flat=True))

        # Save data item-by-item
        for obj in page:
            if skip_models and obj.__class__.__name__.lower() in skip_models:
                continue
            obj.capabilities_cache[display_method] = False
            if obj.pk in ids_with_role:
                obj.capabilities_cache[display_method] = True


def parse_yaml_or_json(vars_str):
    '''
    Attempt to parse a string with variables, and if attempt fails,
    return an empty dictionary.
    '''
    if isinstance(vars_str, dict):
        return vars_str
    try:
        vars_dict = json.loads(vars_str)
    except (ValueError, TypeError):
        try:
            vars_dict = yaml.safe_load(vars_str)
            assert isinstance(vars_dict, dict)
        except (yaml.YAMLError, TypeError, AttributeError, AssertionError):
            vars_dict = {}
    return vars_dict


@memoize()
def get_system_task_capacity():
    '''
    Measure system memory and use it as a baseline for determining the system's capacity
    '''
    from django.conf import settings
    if hasattr(settings, 'SYSTEM_TASK_CAPACITY'):
        return settings.SYSTEM_TASK_CAPACITY
    mem = psutil.virtual_memory()
    total_mem_value = mem.total / 1024 / 1024
    if total_mem_value <= 2048:
        return 50
    return 50 + ((total_mem_value / 1024) - 2) * 75


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


@contextlib.contextmanager
def set_environ(**environ):
    '''
    Temporarily set the process environment variables.

    >>> with set_environ(FOO='BAR'):
    ...   assert os.environ['FOO'] == 'BAR'
    '''
    old_environ = os.environ.copy()
    try:
        os.environ.update(environ)
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


@memoize()
def check_proot_installed():
    '''
    Check that proot is installed.
    '''
    from django.conf import settings
    cmd = [getattr(settings, 'AWX_PROOT_CMD', 'bwrap'), '--version']
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
    from django.conf import settings
    path = tempfile.mkdtemp(prefix='awx_proot_', dir=settings.AWX_PROOT_BASE_PATH)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return path


def wrap_args_with_proot(args, cwd, **kwargs):
    '''
    Wrap existing command line with proot to restrict access to:
     - AWX_PROOT_BASE_PATH (generally, /tmp) (except for own /tmp files)
    For non-isolated nodes:
     - /etc/tower (to prevent obtaining db info or secret key)
     - /var/lib/awx (except for current project)
     - /var/log/tower
     - /var/log/supervisor
    '''
    from django.conf import settings
    new_args = [getattr(settings, 'AWX_PROOT_CMD', 'bwrap'), '--unshare-pid', '--dev-bind', '/', '/']
    hide_paths = [settings.AWX_PROOT_BASE_PATH]
    if not kwargs.get('isolated'):
        hide_paths.extend(['/etc/tower', '/var/lib/awx', '/var/log',
                           settings.PROJECTS_ROOT, settings.JOBOUTPUT_ROOT])
    hide_paths.extend(getattr(settings, 'AWX_PROOT_HIDE_PATHS', None) or [])
    for path in sorted(set(hide_paths)):
        if not os.path.exists(path):
            continue
        path = os.path.realpath(path)
        if os.path.isdir(path):
            new_path = tempfile.mkdtemp(dir=kwargs['proot_temp_dir'])
            os.chmod(new_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        else:
            handle, new_path = tempfile.mkstemp(dir=kwargs['proot_temp_dir'])
            os.close(handle)
            os.chmod(new_path, stat.S_IRUSR | stat.S_IWUSR)
        new_args.extend(['--bind', '%s' %(new_path,), '%s' % (path,)])
    if kwargs.get('isolated'):
        show_paths = [kwargs['private_data_dir']]
    elif 'private_data_dir' in kwargs:
        show_paths = [cwd, kwargs['private_data_dir']]
    else:
        show_paths = [cwd]
    for venv in (
        settings.ANSIBLE_VENV_PATH,
        settings.AWX_VENV_PATH
    ):
        new_args.extend(['--ro-bind', venv, venv])
    show_paths.extend(getattr(settings, 'AWX_PROOT_SHOW_PATHS', None) or [])
    show_paths.extend(kwargs.get('proot_show_paths', []))
    for path in sorted(set(show_paths)):
        if not os.path.exists(path):
            continue
        path = os.path.realpath(path)
        new_args.extend(['--bind', '%s' % (path,), '%s' % (path,)])
    if kwargs.get('isolated'):
        if 'ansible-playbook' in args:
            # playbook runs should cwd to the SCM checkout dir
            new_args.extend(['--chdir', os.path.join(kwargs['private_data_dir'], 'project')])
        else:
            # ad-hoc runs should cwd to the root of the private data dir
            new_args.extend(['--chdir', kwargs['private_data_dir']])
    else:
        new_args.extend(['--chdir', cwd])
    new_args.extend(args)
    return new_args


def get_pk_from_dict(_dict, key):
    '''
    Helper for obtaining a pk from user data dict or None if not present.
    '''
    try:
        val = _dict[key]
        if isinstance(val, object) and hasattr(val, 'id'):
            return val.id  # return id if given model object
        return int(val)
    except (TypeError, KeyError, ValueError):
        return None


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


class NoDefaultProvided(object):
    pass


def getattrd(obj, name, default=NoDefaultProvided):
    """
    Same as getattr(), but allows dot notation lookup
    Discussed in:
    http://stackoverflow.com/questions/11975781
    """

    try:
        return reduce(getattr, name.split("."), obj)
    except AttributeError:
        if default != NoDefaultProvided:
            return default
        raise


current_apps = apps


def set_current_apps(apps):
    global current_apps
    current_apps = apps


def get_current_apps():
    global current_apps
    return current_apps


class OutputEventFilter(object):
    '''
    File-like object that looks for encoded job events in stdout data.
    '''

    EVENT_DATA_RE = re.compile(r'\x1b\[K((?:[A-Za-z0-9+/=]+\x1b\[\d+D)+)\x1b\[K')

    def __init__(self, fileobj=None, event_callback=None, raw_callback=None):
        self._fileobj = fileobj
        self._event_callback = event_callback
        self._raw_callback = raw_callback
        self._counter = 1
        self._start_line = 0
        self._buffer = ''
        self._current_event_data = None

    def __getattr__(self, attr):
        return getattr(self._fileobj, attr)

    def write(self, data):
        if self._fileobj:
            self._fileobj.write(data)
        self._buffer += data
        if self._raw_callback:
            self._raw_callback(data)
        while True:
            match = self.EVENT_DATA_RE.search(self._buffer)
            if not match:
                break
            try:
                base64_data = re.sub(r'\x1b\[\d+D', '', match.group(1))
                event_data = json.loads(base64.b64decode(base64_data))
            except ValueError:
                event_data = {}
            self._emit_event(self._buffer[:match.start()], event_data)
            self._buffer = self._buffer[match.end():]

    def close(self):
        if self._fileobj:
            self._fileobj.close()
        if self._buffer:
            self._emit_event(self._buffer)
            self._buffer = ''

    def _emit_event(self, buffered_stdout, next_event_data=None):
        if self._current_event_data:
            event_data = self._current_event_data
            stdout_chunks = [buffered_stdout]
        elif buffered_stdout:
            event_data = dict(event='verbose')
            stdout_chunks = buffered_stdout.splitlines(True)
        else:
            stdout_chunks = []

        for stdout_chunk in stdout_chunks:
            event_data['counter'] = self._counter
            self._counter += 1
            event_data['stdout'] = stdout_chunk[:-2] if len(stdout_chunk) > 2 else ""
            n_lines = stdout_chunk.count('\n')
            event_data['start_line'] = self._start_line
            event_data['end_line'] = self._start_line + n_lines
            self._start_line += n_lines
            if self._event_callback:
                self._event_callback(event_data)

        if next_event_data.get('uuid', None):
            self._current_event_data = next_event_data
        else:
            self._current_event_data = None


def callback_filter_out_ansible_extra_vars(extra_vars):
    extra_vars_redacted = {}
    extra_vars = parse_yaml_or_json(extra_vars)
    for key, value in extra_vars.iteritems():
        if not key.startswith('ansible_'):
            extra_vars_redacted[key] = value
    return extra_vars_redacted


def get_search_fields(model):
    fields = []
    for field in model._meta.fields:
        if field.name in ('username', 'first_name', 'last_name', 'email',
                          'name', 'description'):
            fields.append(field.name)
    return fields


def has_model_field_prefetched(model_obj, field_name):
    # NOTE: Update this function if django internal implementation changes.
    return getattr(getattr(model_obj, field_name, None),
                   'prefetch_cache_name', '') in getattr(model_obj, '_prefetched_objects_cache', {})
