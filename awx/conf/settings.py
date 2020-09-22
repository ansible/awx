# Python
import contextlib
import logging
import sys
import threading
import time

# Django
from django.conf import LazySettings
from django.conf import settings, UserSettingsHolder
from django.core.cache import cache as django_cache
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction, connection
from django.db.utils import Error as DBError, ProgrammingError
from django.utils.functional import cached_property

# Django REST Framework
from rest_framework.fields import empty, SkipField

import cachetools

# Tower
from awx.main.utils import encrypt_field, decrypt_field
from awx.conf import settings_registry
from awx.conf.models import Setting
from awx.conf.migrations._reencrypt import decrypt_field as old_decrypt_field

# FIXME: Gracefully handle when settings are accessed before the database is
# ready (or during migrations).

logger = logging.getLogger('awx.conf.settings')

SETTING_MEMORY_TTL = 5 if 'callback_receiver' in ' '.join(sys.argv) else 0

# Store a special value to indicate when a setting is not set in the database.
SETTING_CACHE_NOTSET = '___notset___'

# Cannot store None in cache; use a special value instead to indicate None.
# If the special value for None is the same as the "not set" value, then a value
# of None will be equivalent to the setting not being set (and will raise an
# AttributeError if there is no other default defined).
# SETTING_CACHE_NONE = '___none___'
SETTING_CACHE_NONE = SETTING_CACHE_NOTSET

# Cannot store empty list/tuple in cache; use a special value instead to
# indicate an empty list.
SETTING_CACHE_EMPTY_LIST = '___[]___'

# Cannot store empty dict in cache; use a special value instead to indicate
# an empty dict.
SETTING_CACHE_EMPTY_DICT = '___{}___'

# Expire settings from cache after this many seconds.
SETTING_CACHE_TIMEOUT = 60

# Flag indicating whether to store field default values in the cache.
SETTING_CACHE_DEFAULTS = True

__all__ = ['SettingsWrapper', 'get_settings_to_cache', 'SETTING_CACHE_NOTSET']


@contextlib.contextmanager
def _ctit_db_wrapper(trans_safe=False):
    '''
    Wrapper to avoid undesired actions by Django ORM when managing settings
    if only getting a setting, can use trans_safe=True, which will avoid
    throwing errors if the prior context was a broken transaction.
    Any database errors will be logged, but exception will be suppressed.
    '''
    rollback_set = None
    is_atomic = None
    try:
        if trans_safe:
            is_atomic = connection.in_atomic_block
            if is_atomic:
                rollback_set = transaction.get_rollback()
                if rollback_set:
                    logger.debug('Obtaining database settings in spite of broken transaction.')
                    transaction.set_rollback(False)
        yield
    except DBError as exc:
        if trans_safe:
            if 'migrate' not in sys.argv and 'check_migrations' not in sys.argv:
                level = logger.exception
                if isinstance(exc, ProgrammingError):
                    if 'relation' in str(exc) and 'does not exist' in str(exc):
                        # this generally means we can't fetch Tower configuration
                        # because the database hasn't actually finished migrating yet;
                        # this is usually a sign that a service in a container (such as ws_broadcast)
                        # has come up *before* the database has finished migrating, and
                        # especially that the conf.settings table doesn't exist yet
                        level = logger.debug
                level('Database settings are not available, using defaults.')
        else:
            logger.exception('Error modifying something related to database settings.')
    finally:
        if trans_safe and is_atomic and rollback_set:
            transaction.set_rollback(rollback_set)


def filter_sensitive(registry, key, value):
    if registry.is_setting_encrypted(key):
        return '$encrypted$'
    return value


class TransientSetting(object):

    __slots__ = ('pk', 'value')

    def __init__(self, pk, value):
        self.pk = pk
        self.value = value


class EncryptedCacheProxy(object):

    def __init__(self, cache, registry, encrypter=None, decrypter=None):
        """
        This proxy wraps a Django cache backend and overwrites the
        `get`/`set`/`set_many` methods to handle field encryption/decryption
        for sensitive values.

        :param cache: the Django cache backend to proxy to
        :param registry: the settings registry instance used to determine if
                         a field is encrypted or not.
        :param encrypter: a callable used to encrypt field values; defaults to
                          ``awx.main.utils.encrypt_field``
        :param decrypter: a callable used to decrypt field values; defaults to
                          ``awx.main.utils.decrypt_field``
        """

        # These values have to be stored via self.__dict__ in this way to get
        # around the magic __setattr__ method on this class.
        self.__dict__['cache'] = cache
        self.__dict__['registry'] = registry
        self.__dict__['encrypter'] = encrypter or encrypt_field
        self.__dict__['decrypter'] = decrypter or decrypt_field

    def get(self, key, **kwargs):
        value = self.cache.get(key, **kwargs)
        value = self._handle_encryption(self.decrypter, key, value)
        return value

    def set(self, key, value, log=True, **kwargs):
        if log is True:
            logger.debug('cache set(%r, %r, %r)', key, filter_sensitive(self.registry, key, value),
                         SETTING_CACHE_TIMEOUT)
        self.cache.set(
            key,
            self._handle_encryption(self.encrypter, key, value),
            **kwargs
        )

    def set_many(self, data, **kwargs):
        filtered_data = dict(
            (key, filter_sensitive(self.registry, key, value))
            for key, value in data.items()
        )
        logger.debug('cache set_many(%r, %r)', filtered_data, SETTING_CACHE_TIMEOUT)
        for key, value in data.items():
            self.set(key, value, log=False, **kwargs)

    def _handle_encryption(self, method, key, value):
        if value is not empty and self.registry.is_setting_encrypted(key):
            # If the setting exists in the database, we'll use its primary key
            # as part of the AES key when encrypting/decrypting
            obj_id = self.cache.get(Setting.get_cache_id_key(key), default=empty)
            if obj_id is empty:
                logger.info('Efficiency notice: Corresponding id not stored in cache %s',
                            Setting.get_cache_id_key(key))
                obj_id = getattr(self._get_setting_from_db(key), 'pk', None)
            elif obj_id == SETTING_CACHE_NONE:
                obj_id = None
            return method(
                TransientSetting(
                    pk=obj_id,
                    value=value
                ),
                'value'
            )

        # If the field in question isn't an "encrypted" field, this function is
        # a no-op; it just returns the provided value
        return value

    def _get_setting_from_db(self, key):
        field = self.registry.get_setting_field(key)
        if not field.read_only:
            return Setting.objects.filter(key=key, user__isnull=True).order_by('pk').first()

    def __getattr__(self, name):
        return getattr(self.cache, name)

    def __setattr__(self, name, value):
        setattr(self.cache, name, value)


def get_writeable_settings(registry):
    return registry.get_registered_settings(read_only=False)


def get_settings_to_cache(registry):
    return dict([(key, SETTING_CACHE_NOTSET) for key in get_writeable_settings(registry)])


def get_cache_value(value):
    '''Returns the proper special cache setting for a value
    based on instance type.
    '''
    if value is None:
        value = SETTING_CACHE_NONE
    elif isinstance(value, (list, tuple)) and len(value) == 0:
        value = SETTING_CACHE_EMPTY_LIST
    elif isinstance(value, (dict,)) and len(value) == 0:
        value = SETTING_CACHE_EMPTY_DICT
    return value


class SettingsWrapper(UserSettingsHolder):

    @classmethod
    def initialize(cls, cache=None, registry=None):
        """
        Used to initialize and wrap the Django settings context.

        :param cache: the Django cache backend to use for caching setting
        values.  ``django.core.cache`` is used by default.
        :param registry: the settings registry instance used.  The global
        ``awx.conf.settings_registry`` is used by default.
        """
        if not getattr(settings, '_awx_conf_settings', False):
            settings_wrapper = cls(
                settings._wrapped,
                cache=cache or django_cache,
                registry=registry or settings_registry
            )
            settings._wrapped = settings_wrapper

    def __init__(self, default_settings, cache, registry):
        """
        This constructor is generally not called directly, but by
        ``SettingsWrapper.initialize`` at app startup time when settings are
        parsed.
        """

        # These values have to be stored via self.__dict__ in this way to get
        # around the magic __setattr__ method on this class (which is used to
        # store API-assigned settings in the database).
        self.__dict__['default_settings'] = default_settings
        self.__dict__['_awx_conf_settings'] = self
        self.__dict__['_awx_conf_preload_expires'] = None
        self.__dict__['_awx_conf_preload_lock'] = threading.RLock()
        self.__dict__['_awx_conf_init_readonly'] = False
        self.__dict__['cache'] = EncryptedCacheProxy(cache, registry)
        self.__dict__['registry'] = registry

    @cached_property
    def all_supported_settings(self):
        return self.registry.get_registered_settings()

    def _preload_cache(self):
        # Ensure we're only modifying local preload timeout from one thread.
        with self._awx_conf_preload_lock:
            # If local preload timeout has not expired, skip preloading.
            if self._awx_conf_preload_expires and self._awx_conf_preload_expires > time.time():
                return
            # Otherwise update local preload timeout.
            self.__dict__['_awx_conf_preload_expires'] = time.time() + SETTING_CACHE_TIMEOUT
            # Check for any settings that have been defined in Python files and
            # make those read-only to avoid overriding in the database.
            if not self._awx_conf_init_readonly:
                defaults_snapshot = self._get_default('DEFAULTS_SNAPSHOT')
                for key in get_writeable_settings(self.registry):
                    init_default = defaults_snapshot.get(key, None)
                    try:
                        file_default = self._get_default(key)
                    except AttributeError:
                        file_default = None
                    if file_default != init_default and file_default is not None:
                        logger.debug('Setting %s has been marked read-only!', key)
                        self.registry._registry[key]['read_only'] = True
                        self.registry._registry[key]['defined_in_file'] = True
                    self.__dict__['_awx_conf_init_readonly'] = True
        # If local preload timer has expired, check to see if another process
        # has already preloaded the cache and skip preloading if so.
        if self.cache.get('_awx_conf_preload_expires', default=empty) is not empty:
            return
        # Initialize all database-configurable settings with a marker value so
        # to indicate from the cache that the setting is not configured without
        # a database lookup.
        settings_to_cache = get_settings_to_cache(self.registry)
        setting_ids = {}
        # Load all settings defined in the database.
        for setting in Setting.objects.filter(key__in=settings_to_cache.keys(), user__isnull=True).order_by('pk'):
            if settings_to_cache[setting.key] != SETTING_CACHE_NOTSET:
                continue
            if self.registry.is_setting_encrypted(setting.key):
                setting_ids[setting.key] = setting.id
                try:
                    value = decrypt_field(setting, 'value')
                except ValueError as e:
                    #TODO: Remove in Tower 3.3
                    logger.debug('encountered error decrypting field: %s - attempting fallback to old', e)
                    value = old_decrypt_field(setting, 'value')

            else:
                value = setting.value
            settings_to_cache[setting.key] = get_cache_value(value)
        # Load field default value for any settings not found in the database.
        if SETTING_CACHE_DEFAULTS:
            for key, value in settings_to_cache.items():
                if value != SETTING_CACHE_NOTSET:
                    continue
                field = self.registry.get_setting_field(key)
                try:
                    settings_to_cache[key] = get_cache_value(field.get_default())
                    if self.registry.is_setting_encrypted(key):
                        # No database pk, so None will be passed to encryption algorithm
                        setting_ids[key] = SETTING_CACHE_NOTSET
                except SkipField:
                    pass
        # Generate a cache key for each setting and store them all at once.
        settings_to_cache = dict([(Setting.get_cache_key(k), v) for k, v in settings_to_cache.items()])
        for k, id_val in setting_ids.items():
            logger.debug('Saving id in cache for encrypted setting %s, %s',
                         Setting.get_cache_id_key(k), id_val)
            self.cache.cache.set(Setting.get_cache_id_key(k), id_val)
        settings_to_cache['_awx_conf_preload_expires'] = self._awx_conf_preload_expires
        self.cache.set_many(settings_to_cache, timeout=SETTING_CACHE_TIMEOUT)

    def _get_local(self, name, validate=True):
        self._preload_cache()
        cache_key = Setting.get_cache_key(name)
        try:
            cache_value = self.cache.get(cache_key, default=empty)
        except ValueError:
            cache_value = empty
        if cache_value == SETTING_CACHE_NOTSET:
            value = empty
        elif cache_value == SETTING_CACHE_NONE:
            value = None
        elif cache_value == SETTING_CACHE_EMPTY_LIST:
            value = []
        elif cache_value == SETTING_CACHE_EMPTY_DICT:
            value = {}
        else:
            value = cache_value
        field = self.registry.get_setting_field(name)
        if value is empty:
            setting = None
            setting_id = None
            if not field.read_only or name in (
                # these values are read-only - however - we *do* want
                # to fetch their value from the database
                'INSTALL_UUID',
                'AWX_ISOLATED_PRIVATE_KEY',
                'AWX_ISOLATED_PUBLIC_KEY',
            ):
                setting = Setting.objects.filter(key=name, user__isnull=True).order_by('pk').first()
            if setting:
                if getattr(field, 'encrypted', False):
                    value = decrypt_field(setting, 'value')
                    setting_id = setting.id
                else:
                    value = setting.value
            else:
                value = SETTING_CACHE_NOTSET
                if SETTING_CACHE_DEFAULTS:
                    try:
                        value = field.get_default()
                        if getattr(field, 'encrypted', False):
                            setting_id = SETTING_CACHE_NONE
                    except SkipField:
                        pass
            # If None implies not set, convert when reading the value.
            if value is None and SETTING_CACHE_NOTSET == SETTING_CACHE_NONE:
                value = SETTING_CACHE_NOTSET
            if cache_value != value:
                if setting_id:
                    logger.debug('Saving id in cache for encrypted setting %s', cache_key)
                    self.cache.cache.set(Setting.get_cache_id_key(cache_key), setting_id)
                self.cache.set(cache_key, get_cache_value(value), timeout=SETTING_CACHE_TIMEOUT)
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
                    if validate:
                        return field.run_validation(value)
                    else:
                        return value
            except Exception:
                logger.warning(
                    'The current value "%r" for setting "%s" is invalid.',
                    value, name, exc_info=True)
        return empty

    def _get_default(self, name):
        return getattr(self.default_settings, name)

    @property
    def SETTINGS_MODULE(self):
        return self._get_default('SETTINGS_MODULE')

    @cachetools.cached(cache=cachetools.TTLCache(maxsize=2048, ttl=SETTING_MEMORY_TTL))
    def __getattr__(self, name):
        value = empty
        if name in self.all_supported_settings:
            with _ctit_db_wrapper(trans_safe=True):
                value = self._get_local(name)
        if value is not empty:
            return value
        return self._get_default(name)

    def _set_local(self, name, value):
        field = self.registry.get_setting_field(name)
        if field.read_only:
            logger.warning('Attempt to set read only setting "%s".', name)
            raise ImproperlyConfigured('Setting "{}" is read only.'.format(name))

        try:
            data = field.to_representation(value)
            setting_value = field.run_validation(data)
            db_value = field.to_representation(setting_value)
        except Exception as e:
            logger.exception('Unable to assign value "%r" to setting "%s".',
                             value, name, exc_info=True)
            raise e

        setting = Setting.objects.filter(key=name, user__isnull=True).order_by('pk').first()
        if not setting:
            setting = Setting.objects.create(key=name, user=None, value=db_value)
            # post_save handler will delete from cache when added.
        elif setting.value != db_value or type(setting.value) != type(db_value):
            setting.value = db_value
            setting.save(update_fields=['value'])
            # post_save handler will delete from cache when changed.

    def __setattr__(self, name, value):
        if name in self.all_supported_settings:
            with _ctit_db_wrapper():
                self._set_local(name, value)
        else:
            setattr(self.default_settings, name, value)

    def _del_local(self, name):
        field = self.registry.get_setting_field(name)
        if field.read_only:
            logger.warning('Attempt to delete read only setting "%s".', name)
            raise ImproperlyConfigured('Setting "{}" is read only.'.format(name))
        for setting in Setting.objects.filter(key=name, user__isnull=True):
            setting.delete()
            # pre_delete handler will delete from cache.

    def __delattr__(self, name):
        if name in self.all_supported_settings:
            with _ctit_db_wrapper():
                self._del_local(name)
        else:
            delattr(self.default_settings, name)

    def __dir__(self):
        keys = []
        with _ctit_db_wrapper(trans_safe=True):
            for setting in Setting.objects.filter(
                    key__in=self.all_supported_settings, user__isnull=True):
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
        if setting in self.all_supported_settings:
            with _ctit_db_wrapper(trans_safe=True):
                set_locally = Setting.objects.filter(key=setting, user__isnull=True).exists()
        set_on_default = getattr(self.default_settings, 'is_overridden', lambda s: False)(setting)
        return (set_locally or set_on_default)


def __getattr_without_cache__(self, name):
    # Django 1.10 added an optimization to settings lookup:
    # https://code.djangoproject.com/ticket/27625
    # https://github.com/django/django/commit/c1b221a9b913315998a1bcec2f29a9361a74d1ac
    # This change caches settings lookups on the __dict__ of the LazySettings
    # object, which is not okay to do in an environment where settings can
    # change in-process (the entire point of awx's custom settings implementation)
    # This restores the original behavior that *does not* cache.
    if self._wrapped is empty:
        self._setup(name)
    return getattr(self._wrapped, name)


LazySettings.__getattr__ = __getattr_without_cache__
