# Python
import contextlib
import json
import logging
import threading
import time

# Django
from django.conf import settings, UserSettingsHolder
from django.core.cache import cache
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.db import ProgrammingError, OperationalError

# Django REST Framework
from rest_framework.fields import empty, SkipField

# Tower
from awx.conf import settings_registry
from awx.conf.models import Setting

# FIXME: Gracefully handle when settings are accessed before the database is
# ready (or during migrations).

logger = logging.getLogger('awx.conf.settings')

# Store a special value to indicate when a setting is not set in the database.
SETTING_CACHE_NOTSET = '___notset___'

# Cannot store None in memcached; use a special value instead to indicate None.
# If the special value for None is the same as the "not set" value, then a value
# of None will be equivalent to the setting not being set (and will raise an
# AttributeError if there is no other default defined).
# SETTING_CACHE_NONE = '___none___'
SETTING_CACHE_NONE = SETTING_CACHE_NOTSET

# Cannot store empty list/tuple in memcached; use a special value instead to
# indicate an empty list.
SETTING_CACHE_EMPTY_LIST = '___[]___'

# Cannot store empty dict in memcached; use a special value instead to indicate
# an empty dict.
SETTING_CACHE_EMPTY_DICT = '___{}___'

# Expire settings from cache after this many seconds.
SETTING_CACHE_TIMEOUT = 60

# Flag indicating whether to store field default values in the cache.
SETTING_CACHE_DEFAULTS = True

__all__ = ['SettingsWrapper']


@contextlib.contextmanager
def _log_database_error():
    try:
        yield
    except (ProgrammingError, OperationalError) as e:
        logger.warning('Database settings are not available, using defaults (%s)', e, exc_info=True)
    finally:
        pass


class SettingsWrapper(UserSettingsHolder):

    @classmethod
    def initialize(cls):
        if not getattr(settings, '_awx_conf_settings', False):
            settings_wrapper = cls(settings._wrapped)
            settings._wrapped = settings_wrapper

    @classmethod
    def _check_settings(cls, app_configs, **kwargs):
        errors = []
        # FIXME: Warn if database not available!
        for setting in Setting.objects.filter(key__in=settings_registry.get_registered_settings(), user__isnull=True):
            field = settings_registry.get_setting_field(setting.key)
            try:
                field.to_internal_value(setting.value)
            except Exception as e:
                errors.append(checks.Error(str(e)))
        return errors

    def __init__(self, default_settings):
        self.__dict__['default_settings'] = default_settings
        self.__dict__['_awx_conf_settings'] = self
        self.__dict__['_awx_conf_preload_expires'] = None
        self.__dict__['_awx_conf_preload_lock'] = threading.RLock()

    def _get_supported_settings(self):
        return settings_registry.get_registered_settings()

    def _get_writeable_settings(self):
        return settings_registry.get_registered_settings(read_only=False)

    def _get_cache_value(self, value):
        if value is None:
            value = SETTING_CACHE_NONE
        elif isinstance(value, (list, tuple)) and len(value) == 0:
            value = SETTING_CACHE_EMPTY_LIST
        elif isinstance(value, (dict,)) and len(value) == 0:
            value = SETTING_CACHE_EMPTY_DICT
        return value

    def _preload_cache(self):
        # Ensure we're only modifying local preload timeout from one thread.
        with self._awx_conf_preload_lock:
            # If local preload timeout has not expired, skip preloading.
            if self._awx_conf_preload_expires and self._awx_conf_preload_expires > time.time():
                return
            # Otherwise update local preload timeout.
            self.__dict__['_awx_conf_preload_expires'] = time.time() + SETTING_CACHE_TIMEOUT
        # If local preload timer has expired, check to see if another process
        # has already preloaded the cache and skip preloading if so.
        if cache.get('_awx_conf_preload_expires', empty) is not empty:
            return
        # Initialize all database-configurable settings with a marker value so
        # to indicate from the cache that the setting is not configured without
        # a database lookup.
        settings_to_cache = dict([(key, SETTING_CACHE_NOTSET) for key in self._get_writeable_settings()])
        # Load all settings defined in the database.
        for setting in Setting.objects.filter(key__in=settings_to_cache.keys(), user__isnull=True).order_by('pk'):
            if settings_to_cache[setting.key] != SETTING_CACHE_NOTSET:
                continue
            settings_to_cache[setting.key] = self._get_cache_value(setting.value)
        # Load field default value for any settings not found in the database.
        if SETTING_CACHE_DEFAULTS:
            for key, value in settings_to_cache.items():
                if value != SETTING_CACHE_NOTSET:
                    continue
                field = settings_registry.get_setting_field(key)
                try:
                    settings_to_cache[key] = self._get_cache_value(field.get_default())
                except SkipField:
                    pass
        # Generate a cache key for each setting and store them all at once.
        settings_to_cache = dict([(Setting.get_cache_key(k), v) for k, v in settings_to_cache.items()])
        settings_to_cache['_awx_conf_preload_expires'] = self._awx_conf_preload_expires
        logger.debug('cache set_many(%r, %r)', settings_to_cache, SETTING_CACHE_TIMEOUT)
        cache.set_many(settings_to_cache, SETTING_CACHE_TIMEOUT)

    def _get_local(self, name):
        self._preload_cache()
        cache_key = Setting.get_cache_key(name)
        value = cache.get(cache_key, empty)
        logger.debug('cache get(%r, %r) -> %r', cache_key, empty, value)
        if value == SETTING_CACHE_NOTSET:
            value = empty
        elif value == SETTING_CACHE_NONE:
            value = None
        elif value == SETTING_CACHE_EMPTY_LIST:
            value = []
        elif value == SETTING_CACHE_EMPTY_DICT:
            value = {}
        field = settings_registry.get_setting_field(name)
        if value is empty:
            setting = None
            if not field.read_only:
                setting = Setting.objects.filter(key=name, user__isnull=True).order_by('pk').first()
            if setting:
                value = setting.value
                # If None implies not set, convert when reading the value.
                if value is None and SETTING_CACHE_NOTSET == SETTING_CACHE_NONE:
                    value = SETTING_CACHE_NOTSET
            else:
                value = SETTING_CACHE_NOTSET
                if SETTING_CACHE_DEFAULTS:
                    try:
                        value = field.get_default()
                    except SkipField:
                        pass
            logger.debug('cache set(%r, %r, %r)', cache_key, self._get_cache_value(value), SETTING_CACHE_TIMEOUT)
            cache.set(cache_key, self._get_cache_value(value), SETTING_CACHE_TIMEOUT)
        if value == SETTING_CACHE_NOTSET and not SETTING_CACHE_DEFAULTS:
            try:
                value = field.get_default()
            except SkipField:
                pass
        if value not in (empty, SETTING_CACHE_NOTSET):
            try:
                if field.read_only:
                    internal_value = field.to_internal_value(value)
                    field.run_validators(internal_value)
                    return internal_value
                else:
                    return field.run_validation(value)
            except:
                logger.warning('The current value "%r" for setting "%s" is invalid.', value, name, exc_info=True)
        return empty

    def _get_default(self, name):
        return getattr(self.default_settings, name)

    @property
    def SETTINGS_MODULE(self):
        return self._get_default('SETTINGS_MODULE')

    def __getattr__(self, name):
        value = empty
        if name in self._get_supported_settings():
            with _log_database_error():
                value = self._get_local(name)
        if value is not empty:
            return value
        return self._get_default(name)

    def _set_local(self, name, value):
        field = settings_registry.get_setting_field(name)
        if field.read_only:
            logger.warning('Attempt to set read only setting "%s".', name)
            raise ImproperlyConfigured('Setting "%s" is read only.'.format(name))

        try:
            data = field.to_representation(value)
            setting_value = field.run_validation(data)
            db_value = field.to_representation(setting_value)
        except Exception as e:
            logger.exception('Unable to assign value "%r" to setting "%s".', value, name, exc_info=True)
            raise e

        # Always encode "raw" strings as JSON.
        if isinstance(db_value, basestring):
            db_value = json.dumps(db_value)
        setting = Setting.objects.filter(key=name, user__isnull=True).order_by('pk').first()
        if not setting:
            setting = Setting.objects.create(key=name, user=None, value=db_value)
            # post_save handler will delete from cache when added.
        elif setting.value != db_value or type(setting.value) != type(db_value):
            setting.value = db_value
            setting.save(update_fields=['value'])
            # post_save handler will delete from cache when changed.

    def __setattr__(self, name, value):
        if name in self._get_supported_settings():
            with _log_database_error():
                self._set_local(name, value)
        else:
            setattr(self.default_settings, name, value)

    def _del_local(self, name):
        field = settings_registry.get_setting_field(name)
        if field.read_only:
            logger.warning('Attempt to delete read only setting "%s".', name)
            raise ImproperlyConfigured('Setting "%s" is read only.'.format(name))
        for setting in Setting.objects.filter(key=name, user__isnull=True):
            setting.delete()
            # pre_delete handler will delete from cache.

    def __delattr__(self, name):
        if name in self._get_supported_settings():
            with _log_database_error():
                self._del_local(name)
        else:
            delattr(self.default_settings, name)

    def __dir__(self):
        keys = []
        with _log_database_error():
            for setting in Setting.objects.filter(key__in=self._get_supported_settings(), user__isnull=True):
                # Skip returning settings that have been overridden but are
                # considered to be "not set".
                if setting.value is None and SETTING_CACHE_NOTSET == SETTING_CACHE_NONE:
                    continue
                if setting.key not in keys:
                    keys.append(str(setting.key))
        for key in dir(self.default_settings):
            if key not in keys:
                keys.append(key)
        return keys

    def is_overridden(self, setting):
        set_locally = False
        if setting in self._get_supported_settings():
            with _log_database_error():
                set_locally = Setting.objects.filter(key=setting, user__isnull=True).exists()
        set_on_default = getattr(self.default_settings, 'is_overridden', lambda s: False)(setting)
        return (set_locally or set_on_default)
