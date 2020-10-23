# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import yaml
import logging
import os
import re
import subprocess
import stat
import urllib.parse
import threading
import contextlib
import tempfile
import psutil
from functools import reduce, wraps

from decimal import Decimal

# Django
from django.core.exceptions import ObjectDoesNotExist, FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor
)
from django.db.models.query import QuerySet
from django.db.models import Q

# Django REST Framework
from rest_framework.exceptions import ParseError
from django.utils.encoding import smart_str
from django.utils.text import slugify
from django.apps import apps

# AWX
from awx.conf.license import get_license

logger = logging.getLogger('awx.main.utils')

__all__ = [
    'get_object_or_400', 'camelcase_to_underscore', 'underscore_to_camelcase', 'memoize',
    'memoize_delete', 'get_ansible_version', 'get_licenser', 'get_awx_http_client_headers',
    'get_awx_version', 'update_scm_url', 'get_type_for_model', 'get_model_for_type',
    'copy_model_by_class', 'copy_m2m_relationships',
    'prefetch_page_capabilities', 'to_python_boolean', 'ignore_inventory_computed_fields',
    'ignore_inventory_group_removal', '_inventory_updates', 'get_pk_from_dict', 'getattrd',
    'getattr_dne', 'NoDefaultProvided', 'get_current_apps', 'set_current_apps',
    'extract_ansible_vars', 'get_search_fields', 'get_system_task_capacity',
    'get_cpu_capacity', 'get_mem_capacity', 'wrap_args_with_proot', 'build_proot_temp_dir',
    'check_proot_installed', 'model_to_dict', 'NullablePromptPseudoField',
    'model_instance_diff', 'parse_yaml_or_json', 'RequireDebugTrueOrTest',
    'has_model_field_prefetched', 'set_environ', 'IllegalArgumentError',
    'get_custom_venv_choices', 'get_external_account', 'task_manager_bulk_reschedule',
    'schedule_task_manager', 'classproperty', 'create_temporary_fifo', 'truncate_stdout'
]


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


def to_python_boolean(value, allow_none=False):
    value = str(value)
    if value.lower() in ('true', '1', 't'):
        return True
    elif value.lower() in ('false', '0', 'f'):
        return False
    elif allow_none and value.lower() in ('none', 'null'):
        return None
    else:
        raise ValueError(_(u'Unable to convert "%s" to boolean') % value)


def camelcase_to_underscore(s):
    '''
    Convert CamelCase names to lowercase_with_underscore.
    '''
    s = re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s)
    return s.lower().strip('_')


def underscore_to_camelcase(s):
    '''
    Convert lowercase_with_underscore names to CamelCase.
    '''
    return ''.join(x.capitalize() or '_' for x in s.split('_'))



class RequireDebugTrueOrTest(logging.Filter):
    '''
    Logging filter to output when in DEBUG mode or running tests.
    '''

    def filter(self, record):
        from django.conf import settings
        return settings.DEBUG or settings.IS_TESTING()


class IllegalArgumentError(ValueError):
    pass


def get_memoize_cache():
    from django.core.cache import cache
    return cache


def memoize(ttl=60, cache_key=None, track_function=False, cache=None):
    '''
    Decorator to wrap a function and cache its result.
    '''
    if cache_key and track_function:
        raise IllegalArgumentError("Can not specify cache_key when track_function is True")
    cache = cache or get_memoize_cache()

    def memoize_decorator(f):
        @wraps(f)
        def _memoizer(*args, **kwargs):
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

        return _memoizer

    return memoize_decorator


def memoize_delete(function_name):
    cache = get_memoize_cache()
    return cache.delete(function_name)


@memoize()
def get_ansible_version():
    '''
    Return Ansible version installed.
    Ansible path needs to be provided to account for custom virtual environments
    '''
    try:
        proc = subprocess.Popen(['ansible', '--version'],
                                stdout=subprocess.PIPE)
        result = smart_str(proc.communicate()[0])
        return result.split('\n')[0].replace('ansible', '').strip()
    except Exception:
        return 'unknown'


def get_awx_version():
    '''
    Return AWX version as reported by setuptools.
    '''
    from awx import __version__
    try:
        import pkg_resources
        return pkg_resources.require('awx')[0].version
    except Exception:
        return __version__


def get_awx_http_client_headers():
    license = get_license().get('license_type', 'UNLICENSED')
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': '{} {} ({})'.format(
            'AWX' if license == 'open' else 'Red Hat Ansible Tower',
            get_awx_version(),
            license
        )
    }
    return headers


def get_licenser(*args, **kwargs):
    from awx.main.utils.licensing import Licenser, OpenLicense
    try:
        if os.path.exists('/var/lib/awx/.tower_version'):
            return Licenser(*args, **kwargs)
        else:
            return OpenLicense()
    except Exception as e:
        raise ValueError(_('Error importing Tower License: %s') % e)


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
    if scm_type not in ('git', 'hg', 'svn', 'insights', 'archive'):
        raise ValueError(_('Unsupported SCM type "%s"') % str(scm_type))
    if not url.strip():
        return ''
    parts = urllib.parse.urlsplit(url)
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
            parts = urllib.parse.urlsplit('git+ssh://%s' % modified_url)
        # Handle local paths specified without file scheme (e.g. /path/to/foo).
        # Only supported by git and hg.
        elif scm_type in ('git', 'hg'):
            if not url.startswith('/'):
                parts = urllib.parse.urlsplit('file:///%s' % url)
            else:
                parts = urllib.parse.urlsplit('file://%s' % url)
        else:
            raise ValueError(_('Invalid %s URL') % scm_type)

    # Validate that scheme is valid for given scm_type.
    scm_type_schemes = {
        'git': ('ssh', 'git', 'git+ssh', 'http', 'https', 'ftp', 'ftps', 'file'),
        'hg': ('http', 'https', 'ssh', 'file'),
        'svn': ('http', 'https', 'svn', 'svn+ssh', 'file'),
        'insights': ('http', 'https'),
        'archive': ('http', 'https'),
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

    if netloc_username and parts.scheme != 'file' and scm_type not in ("insights", "archive"):
        netloc = u':'.join([urllib.parse.quote(x,safe='') for x in (netloc_username, netloc_password) if x])
    else:
        netloc = u''
    netloc = u'@'.join(filter(None, [netloc, parts.hostname]))
    if parts.port:
        netloc = u':'.join([netloc, str(parts.port)])
    new_url = urllib.parse.urlunsplit([parts.scheme, netloc, parts.path,
                                       parts.query, parts.fragment])
    if scp_format and parts.scheme == 'git+ssh':
        new_url = new_url.replace('git+ssh://', '', 1).replace('/', ':', 1)
    return new_url


def get_allowed_fields(obj, serializer_mapping):

    if serializer_mapping is not None and obj.__class__ in serializer_mapping:
        serializer_actual = serializer_mapping[obj.__class__]()
        allowed_fields = [x for x in serializer_actual.fields if not serializer_actual.fields[x].read_only] + ['id']
    else:
        allowed_fields = [x.name for x in obj._meta.fields]

    ACTIVITY_STREAM_FIELD_EXCLUSIONS = {
        'user': ['last_login'],
        'oauth2accesstoken': ['last_used'],
        'oauth2application': ['client_secret']
    }
    model_name = obj._meta.model_name
    fields_excluded = ACTIVITY_STREAM_FIELD_EXCLUSIONS.get(model_name, [])
    # see definition of from_db for CredentialType
    # injection logic of any managed types are incompatible with activity stream
    if model_name == 'credentialtype' and obj.managed_by_tower and obj.namespace:
        fields_excluded.extend(['inputs', 'injectors'])
    if fields_excluded:
        allowed_fields = [f for f in allowed_fields if f not in fields_excluded]
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
        isinstance(field_val, str) and
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

    for field_name in allowed_fields:
        attr_d[field_name] = _convert_model_field_for_display(obj, field_name, password_fields=password_fields)
    return attr_d


class CharPromptDescriptor:
    """Class used for identifying nullable launch config fields from class
    ex. Schedule.limit
    """
    def __init__(self, field):
        self.field = field


class NullablePromptPseudoField:
    """
    Interface for pseudo-property stored in `char_prompts` dict
    Used in LaunchTimeConfig and submodels, defined here to avoid circular imports
    """
    def __init__(self, field_name):
        self.field_name = field_name

    @cached_property
    def field_descriptor(self):
        return CharPromptDescriptor(self)

    def __get__(self, instance, type=None):
        if instance is None:
            # for inspection on class itself
            return self.field_descriptor
        return instance.char_prompts.get(self.field_name, None)

    def __set__(self, instance, value):
        if value in (None, {}):
            instance.char_prompts.pop(self.field_name, None)
        else:
            instance.char_prompts[self.field_name] = value


def copy_model_by_class(obj1, Class2, fields, kwargs):
    '''
    Creates a new unsaved object of type Class2 using the fields from obj1
    values in kwargs can override obj1
    '''
    create_kwargs = {}
    for field_name in fields:
        descriptor = getattr(Class2, field_name)
        if isinstance(descriptor, ForwardManyToOneDescriptor):  # ForeignKey
            # Foreign keys can be specified as field_name or field_name_id.
            id_field_name = '%s_id' % field_name
            if field_name in kwargs:
                value = kwargs[field_name]
            elif id_field_name in kwargs:
                value = kwargs[id_field_name]
            else:
                value = getattr(obj1, id_field_name)
            if hasattr(value, 'id'):
                value = value.id
            create_kwargs[id_field_name] = value
        elif isinstance(descriptor, CharPromptDescriptor):
            # difficult case of copying one launch config to another launch config
            new_val = None
            if field_name in kwargs:
                new_val = kwargs[field_name]
            elif hasattr(obj1, 'char_prompts'):
                if field_name in obj1.char_prompts:
                    new_val = obj1.char_prompts[field_name]
            elif hasattr(obj1, field_name):
                # extremely rare case where a template spawns a launch config - sliced jobs
                new_val = getattr(obj1, field_name)
            if new_val is not None:
                create_kwargs.setdefault('char_prompts', {})
                create_kwargs['char_prompts'][field_name] = new_val
        elif isinstance(descriptor, ManyToManyDescriptor):
            continue  # not copied in this method
        elif field_name in kwargs:
            if field_name == 'extra_vars' and isinstance(kwargs[field_name], dict):
                create_kwargs[field_name] = json.dumps(kwargs['extra_vars'])
            elif not isinstance(Class2._meta.get_field(field_name), (ForeignObjectRel, ManyToManyField)):
                create_kwargs[field_name] = kwargs[field_name]
        elif hasattr(obj1, field_name):
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
            try:
                field_obj = obj1._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            if isinstance(field_obj, ManyToManyField):
                # Many to Many can be specified as field_name
                src_field_value = getattr(obj1, field_name)
                if kwargs and field_name in kwargs:
                    override_field_val = kwargs[field_name]
                    if isinstance(override_field_val, (set, list, QuerySet)):
                        getattr(obj2, field_name).add(*override_field_val)
                        continue
                    if override_field_val.__class__.__name__ == 'ManyRelatedManager':
                        src_field_value = override_field_val
                dest_field = getattr(obj2, field_name)
                dest_field.add(*list(src_field_value.all().values_list('id', flat=True)))


def get_type_for_model(model):
    '''
    Return type name for a given model class.
    '''
    opts = model._meta.concrete_model._meta
    return camelcase_to_underscore(opts.object_name)


def get_model_for_type(type_name):
    '''
    Return model class for a given type name.
    '''
    model_str = underscore_to_camelcase(type_name)
    if model_str == 'User':
        use_app = 'auth'
    else:
        use_app = 'main'
    return apps.get_model(use_app, model_str)


def prefetch_page_capabilities(model, page, prefetch_list, user):
    '''
    Given a `page` list of objects, a nested dictionary of user_capabilities
    are returned by id, ex.
    {
        4: {'edit': True, 'start': True},
        6: {'edit': False, 'start': False}
    }
    Each capability is produced for all items in the page in a single query

    Examples of prefetch language:
    prefetch_list = ['admin', 'execute']
      --> prefetch the admin (edit) and execute (start) permissions for
          items in list for current user
    prefetch_list = ['inventory.admin']
      --> prefetch the related inventory FK permissions for current user,
          and put it into the object's cache
    prefetch_list = [{'copy': ['inventory.admin', 'project.admin']}]
      --> prefetch logical combination of admin permission to inventory AND
          project, put into cache dictionary as "copy"
    '''
    page_ids = [obj.id for obj in page]
    mapping = {}
    for obj in page:
        mapping[obj.id] = {}

    for prefetch_entry in prefetch_list:

        display_method = None
        if type(prefetch_entry) is dict:
            display_method = list(prefetch_entry.keys())[0]
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
            mapping[obj.pk][display_method] = bool(obj.pk in ids_with_role)

    return mapping


def validate_vars_type(vars_obj):
    if not isinstance(vars_obj, dict):
        vars_type = type(vars_obj)
        if hasattr(vars_type, '__name__'):
            data_type = vars_type.__name__
        else:
            data_type = str(vars_type)
        raise AssertionError(
            _('Input type `{data_type}` is not a dictionary').format(
                data_type=data_type)
        )


def parse_yaml_or_json(vars_str, silent_failure=True):
    '''
    Attempt to parse a string of variables.
    First, with JSON parser, if that fails, then with PyYAML.
    If both attempts fail, return an empty dictionary if `silent_failure`
    is True, re-raise combination error if `silent_failure` if False.
    '''
    if isinstance(vars_str, dict):
        return vars_str
    elif isinstance(vars_str, str) and vars_str == '""':
        return {}

    try:
        vars_dict = json.loads(vars_str)
        validate_vars_type(vars_dict)
    except (ValueError, TypeError, AssertionError) as json_err:
        try:
            vars_dict = yaml.safe_load(vars_str)
            # Can be None if '---'
            if vars_dict is None:
                vars_dict = {}
            validate_vars_type(vars_dict)
            if not silent_failure:
                # is valid YAML, check that it is compatible with JSON
                try:
                    json.dumps(vars_dict)
                except (ValueError, TypeError, AssertionError) as json_err2:
                    raise ParseError(_(
                        'Variables not compatible with JSON standard (error: {json_error})').format(
                            json_error=str(json_err2)))
        except (yaml.YAMLError, TypeError, AttributeError, AssertionError) as yaml_err:
            if silent_failure:
                return {}
            raise ParseError(_(
                'Cannot parse as JSON (error: {json_error}) or '
                'YAML (error: {yaml_error}).').format(
                    json_error=str(json_err), yaml_error=str(yaml_err)))
    return vars_dict


def get_cpu_capacity():
    from django.conf import settings
    settings_forkcpu = getattr(settings, 'SYSTEM_TASK_FORKS_CPU', None)
    env_forkcpu = os.getenv('SYSTEM_TASK_FORKS_CPU', None)

    settings_abscpu = getattr(settings, 'SYSTEM_TASK_ABS_CPU', None)
    env_abscpu = os.getenv('SYSTEM_TASK_ABS_CPU', None)

    if env_abscpu is not None:
        return 0, int(env_abscpu)
    elif settings_abscpu is not None:
        return 0, int(settings_abscpu)

    cpu = psutil.cpu_count()

    if env_forkcpu:
        forkcpu = int(env_forkcpu)
    elif settings_forkcpu:
        forkcpu = int(settings_forkcpu)
    else:
        forkcpu = 4
    return (cpu, cpu * forkcpu)


def get_mem_capacity():
    from django.conf import settings
    settings_forkmem = getattr(settings, 'SYSTEM_TASK_FORKS_MEM', None)
    env_forkmem = os.getenv('SYSTEM_TASK_FORKS_MEM', None)

    settings_absmem = getattr(settings, 'SYSTEM_TASK_ABS_MEM', None)
    env_absmem = os.getenv('SYSTEM_TASK_ABS_MEM', None)

    if env_absmem is not None:
        return 0, int(env_absmem)
    elif settings_absmem is not None:
        return 0, int(settings_absmem)

    if env_forkmem:
        forkmem = int(env_forkmem)
    elif settings_forkmem:
        forkmem = int(settings_forkmem)
    else:
        forkmem = 100

    mem = psutil.virtual_memory().total
    return (mem, max(1, ((mem // 1024 // 1024) - 2048) // forkmem))


def get_system_task_capacity(scale=Decimal(1.0), cpu_capacity=None, mem_capacity=None):
    '''
    Measure system memory and use it as a baseline for determining the system's capacity
    '''
    from django.conf import settings
    settings_forks = getattr(settings, 'SYSTEM_TASK_FORKS_CAPACITY', None)
    env_forks = os.getenv('SYSTEM_TASK_FORKS_CAPACITY', None)

    if env_forks:
        return int(env_forks)
    elif settings_forks:
        return int(settings_forks)

    if cpu_capacity is None:
        _, cpu_cap = get_cpu_capacity()
    else:
        cpu_cap = cpu_capacity
    if mem_capacity is None:
        _, mem_cap = get_mem_capacity()
    else:
        mem_cap = mem_capacity
    return min(mem_cap, cpu_cap) + ((max(mem_cap, cpu_cap) - min(mem_cap, cpu_cap)) * scale)


_inventory_updates = threading.local()
_task_manager = threading.local()


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


def _schedule_task_manager():
    from awx.main.scheduler.tasks import run_task_manager
    from django.db import connection
    # runs right away if not in transaction
    connection.on_commit(lambda: run_task_manager.delay())


@contextlib.contextmanager
def task_manager_bulk_reschedule():
    """Context manager to avoid submitting task multiple times.
    """
    try:
        previous_flag = getattr(_task_manager, 'bulk_reschedule', False)
        previous_value = getattr(_task_manager, 'needs_scheduling', False)
        _task_manager.bulk_reschedule = True
        _task_manager.needs_scheduling = False
        yield
    finally:
        _task_manager.bulk_reschedule = previous_flag
        if _task_manager.needs_scheduling:
            _schedule_task_manager()
        _task_manager.needs_scheduling = previous_value


def schedule_task_manager():
    if getattr(_task_manager, 'bulk_reschedule', False):
        _task_manager.needs_scheduling = True
        return
    _schedule_task_manager()


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
    except (OSError, ValueError) as e:
        if isinstance(e, ValueError) or getattr(e, 'errno', 1) != 2:  # ENOENT, no such file or directory
            logger.exception('bwrap unavailable for unexpected reason.')
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
    cwd = os.path.realpath(cwd)
    new_args = [getattr(settings, 'AWX_PROOT_CMD', 'bwrap'), '--unshare-pid', '--dev-bind', '/', '/', '--proc', '/proc']
    hide_paths = [settings.AWX_PROOT_BASE_PATH]
    if not kwargs.get('isolated'):
        hide_paths.extend(['/etc/tower', '/var/lib/awx', '/var/log', '/etc/ssh',
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
        settings.AWX_VENV_PATH,
        kwargs.get('proot_custom_virtualenv')
    ):
        if venv:
            new_args.extend(['--ro-bind', venv, venv])
    show_paths.extend(getattr(settings, 'AWX_PROOT_SHOW_PATHS', None) or [])
    show_paths.extend(kwargs.get('proot_show_paths', []))
    for path in sorted(set(show_paths)):
        if not os.path.exists(path):
            continue
        path = os.path.realpath(path)
        new_args.extend(['--bind', '%s' % (path,), '%s' % (path,)])
    if kwargs.get('isolated'):
        if '/bin/ansible-playbook' in ' '.join(args):
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


def getattr_dne(obj, name, notfound=ObjectDoesNotExist):
    try:
        return getattr(obj, name)
    except notfound:
        return None


current_apps = apps


def set_current_apps(apps):
    global current_apps
    current_apps = apps


def get_current_apps():
    global current_apps
    return current_apps


def get_custom_venv_choices(custom_paths=None):
    from django.conf import settings
    custom_paths = custom_paths or settings.CUSTOM_VENV_PATHS
    all_venv_paths = [settings.BASE_VENV_PATH] + custom_paths
    custom_venv_choices = []

    for custom_venv_path in all_venv_paths:
        try:
            if os.path.exists(custom_venv_path):
                custom_venv_choices.extend([
                    os.path.join(custom_venv_path, x, '')
                    for x in os.listdir(custom_venv_path)
                    if x != 'awx' and
                    os.path.isdir(os.path.join(custom_venv_path, x)) and
                    os.path.exists(os.path.join(custom_venv_path, x, 'bin', 'activate'))
                ])
        except Exception:
            logger.exception("Encountered an error while discovering custom virtual environments.")
    return custom_venv_choices


def is_ansible_variable(key):
    return key.startswith('ansible_')


def extract_ansible_vars(extra_vars):
    extra_vars = parse_yaml_or_json(extra_vars)
    ansible_vars = set([])
    for key in list(extra_vars.keys()):
        if is_ansible_variable(key):
            extra_vars.pop(key)
            ansible_vars.add(key)
    return (extra_vars, ansible_vars)


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


def get_external_account(user):
    from django.conf import settings
    account_type = None
    if getattr(settings, 'AUTH_LDAP_SERVER_URI', None):
        try:
            if user.pk and user.profile.ldap_dn and not user.has_usable_password():
                account_type = "ldap"
        except AttributeError:
            pass
    if (getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or
            getattr(settings, 'SOCIAL_AUTH_GITHUB_KEY', None) or
            getattr(settings, 'SOCIAL_AUTH_GITHUB_ORG_KEY', None) or
            getattr(settings, 'SOCIAL_AUTH_GITHUB_TEAM_KEY', None) or
            getattr(settings, 'SOCIAL_AUTH_SAML_ENABLED_IDPS', None)) and user.social_auth.all():
        account_type = "social"
    if (getattr(settings, 'RADIUS_SERVER', None) or
            getattr(settings, 'TACACSPLUS_HOST', None)) and user.enterprise_auth.all():
        account_type = "enterprise"
    return account_type


class classproperty:

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, instance, ownerclass):
        return self.fget(ownerclass)


def create_temporary_fifo(data):
    """Open fifo named pipe in a new thread using a temporary file path. The
    thread blocks until data is read from the pipe.
    Returns the path to the fifo.
    :param data(bytes): Data to write to the pipe.
    """
    path = os.path.join(tempfile.mkdtemp(), next(tempfile._get_candidate_names()))
    os.mkfifo(path, stat.S_IRUSR | stat.S_IWUSR)

    threading.Thread(
        target=lambda p, d: open(p, 'wb').write(d),
        args=(path, data)
    ).start()
    return path


def truncate_stdout(stdout, size):
    from awx.main.constants import ANSI_SGR_PATTERN

    if size <= 0 or len(stdout) <= size:
        return stdout

    stdout = stdout[:(size - 1)] + u'\u2026'
    set_count, reset_count = 0, 0
    for m in ANSI_SGR_PATTERN.finditer(stdout):
        if m.group() == u'\u001b[0m':
            reset_count += 1
        else:
            set_count += 1

    return stdout + u'\u001b[0m' * (set_count - reset_count)
