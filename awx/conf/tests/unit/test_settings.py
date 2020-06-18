# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from contextlib import contextmanager
import codecs
from uuid import uuid4
import time

from django.conf import LazySettings
from django.core.cache.backends.locmem import LocMemCache
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
import pytest

from awx.conf import models, fields
from awx.conf.settings import SettingsWrapper, EncryptedCacheProxy, SETTING_CACHE_NOTSET
from awx.conf.registry import SettingsRegistry

from awx.main.utils import encrypt_field, decrypt_field


@contextmanager
def apply_patches(_patches):
    [p.start() for p in _patches]
    yield
    [p.stop() for p in _patches]


@pytest.fixture()
def settings(request):
    """
    This fixture initializes a Django settings object that wraps our
    `awx.conf.settings.SettingsWrapper` and passes it as an argument into the
    test function.

    This mimics the work done by `awx.conf.settings.SettingsWrapper.initialize`
    on `django.conf.settings`.
    """
    cache = LocMemCache(str(uuid4()), {})  # make a new random cache each time
    settings = LazySettings()
    registry = SettingsRegistry(settings)
    defaults = {}

    # @pytest.mark.defined_in_file can be used to mark specific setting values
    # as "defined in a settings file".  This is analogous to manually
    # specifying a setting on the filesystem (e.g., in a local_settings.py in
    # development, or in /etc/tower/conf.d/<something>.py)
    for marker in request.node.own_markers:
        if marker.name == 'defined_in_file':
            defaults = marker.kwargs

    defaults['DEFAULTS_SNAPSHOT'] = {}
    settings.configure(**defaults)
    settings._wrapped = SettingsWrapper(settings._wrapped,
                                        cache,
                                        registry)
    return settings


@pytest.mark.defined_in_file(DEBUG=True)
def test_unregistered_setting(settings):
    "native Django settings are not stored in DB, and aren't cached"
    assert settings.DEBUG is True
    assert settings.cache.get('DEBUG') is None


def test_read_only_setting(settings):
    settings.registry.register(
        'AWX_READ_ONLY',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        default='NO-EDITS',
        read_only=True
    )
    assert settings.AWX_READ_ONLY == 'NO-EDITS'
    assert len(settings.registry.get_registered_settings(read_only=False)) == 0
    settings = settings.registry.get_registered_settings(read_only=True)
    assert settings == ['AWX_READ_ONLY']


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
@pytest.mark.parametrize('read_only', [True, False])
def test_setting_defined_in_file(settings, read_only):
    kwargs = {'read_only': True} if read_only else {}
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        **kwargs
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert len(settings.registry.get_registered_settings(read_only=False)) == 0
    settings = settings.registry.get_registered_settings(read_only=True)
    assert settings == ['AWX_SOME_SETTING']


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_setting_defined_in_file_with_empty_default(settings):
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        default='',
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert len(settings.registry.get_registered_settings(read_only=False)) == 0
    settings = settings.registry.get_registered_settings(read_only=True)
    assert settings == ['AWX_SOME_SETTING']


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_setting_defined_in_file_with_specific_default(settings):
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        default=123
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert len(settings.registry.get_registered_settings(read_only=False)) == 0
    settings = settings.registry.get_registered_settings(read_only=True)
    assert settings == ['AWX_SOME_SETTING']


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_read_only_defaults_are_cached(settings):
    "read-only settings are stored in the cache"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert settings.cache.get('AWX_SOME_SETTING') == 'DEFAULT'


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_cache_respects_timeout(settings):
    "only preload the cache every SETTING_CACHE_TIMEOUT settings"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )

    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    cache_expiration = settings.cache.get('_awx_conf_preload_expires')
    assert cache_expiration > time.time()

    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert settings.cache.get('_awx_conf_preload_expires') == cache_expiration


def test_default_setting(settings, mocker):
    "settings that specify a default are inserted into the cache"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        default='DEFAULT'
    )

    settings_to_cache = mocker.Mock(**{'order_by.return_value': []})
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=settings_to_cache):
        assert settings.AWX_SOME_SETTING == 'DEFAULT'
        assert settings.cache.get('AWX_SOME_SETTING') == 'DEFAULT'


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_setting_is_from_setting_file(settings, mocker):
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert settings.registry.get_setting_field('AWX_SOME_SETTING').defined_in_file is True


def test_setting_is_not_from_setting_file(settings, mocker):
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        default='DEFAULT'
    )

    settings_to_cache = mocker.Mock(**{'order_by.return_value': []})
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=settings_to_cache):
        assert settings.AWX_SOME_SETTING == 'DEFAULT'
        assert settings.registry.get_setting_field('AWX_SOME_SETTING').defined_in_file is False


def test_empty_setting(settings, mocker):
    "settings with no default and no defined value are not valid"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )

    mocks = mocker.Mock(**{
        'order_by.return_value': mocker.Mock(**{
            '__iter__': lambda self: iter([]),
            'first.return_value': None
        }),
    })
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=mocks):
        with pytest.raises(AttributeError):
            settings.AWX_SOME_SETTING
        assert settings.cache.get('AWX_SOME_SETTING') == SETTING_CACHE_NOTSET


def test_setting_from_db(settings, mocker):
    "settings can be loaded from the database"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        default='DEFAULT'
    )

    setting_from_db = mocker.Mock(key='AWX_SOME_SETTING', value='FROM_DB')
    mocks = mocker.Mock(**{
        'order_by.return_value': mocker.Mock(**{
            '__iter__': lambda self: iter([setting_from_db]),
            'first.return_value': setting_from_db
        }),
    })
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=mocks):
        assert settings.AWX_SOME_SETTING == 'FROM_DB'
        assert settings.cache.get('AWX_SOME_SETTING') == 'FROM_DB'


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_read_only_setting_assignment(settings):
    "read-only settings cannot be overwritten"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    with pytest.raises(ImproperlyConfigured):
        settings.AWX_SOME_SETTING = 'CHANGED'
    assert settings.AWX_SOME_SETTING == 'DEFAULT'


def test_db_setting_create(settings, mocker):
    "settings are stored in the database when set for the first time"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )

    setting_list = mocker.Mock(**{'order_by.return_value.first.return_value': None})
    with apply_patches([
        mocker.patch('awx.conf.models.Setting.objects.filter',
                     return_value=setting_list),
        mocker.patch('awx.conf.models.Setting.objects.create', mocker.Mock())
    ]):
        settings.AWX_SOME_SETTING = 'NEW-VALUE'

    models.Setting.objects.create.assert_called_with(
        key='AWX_SOME_SETTING',
        user=None,
        value='NEW-VALUE'
    )


def test_db_setting_update(settings, mocker):
    "settings are updated in the database when their value changes"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )

    existing_setting = mocker.Mock(key='AWX_SOME_SETTING', value='FROM_DB')
    setting_list = mocker.Mock(**{
        'order_by.return_value.first.return_value': existing_setting
    })
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=setting_list):
        settings.AWX_SOME_SETTING = 'NEW-VALUE'

    assert existing_setting.value == 'NEW-VALUE'
    existing_setting.save.assert_called_with(update_fields=['value'])


def test_db_setting_deletion(settings, mocker):
    "settings are auto-deleted from the database"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )

    existing_setting = mocker.Mock(key='AWX_SOME_SETTING', value='FROM_DB')
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=[existing_setting]):
        del settings.AWX_SOME_SETTING

    assert existing_setting.delete.call_count == 1


@pytest.mark.defined_in_file(AWX_SOME_SETTING='DEFAULT')
def test_read_only_setting_deletion(settings):
    "read-only settings cannot be deleted"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    with pytest.raises(ImproperlyConfigured):
        del settings.AWX_SOME_SETTING
    assert settings.AWX_SOME_SETTING == 'DEFAULT'


def test_charfield_properly_sets_none(settings, mocker):
    "see: https://github.com/ansible/ansible-tower/issues/5322"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        allow_null=True
    )

    setting_list = mocker.Mock(**{'order_by.return_value.first.return_value': None})
    with apply_patches([
        mocker.patch('awx.conf.models.Setting.objects.filter',
                     return_value=setting_list),
        mocker.patch('awx.conf.models.Setting.objects.create', mocker.Mock())
    ]):
        settings.AWX_SOME_SETTING = None

    models.Setting.objects.create.assert_called_with(
        key='AWX_SOME_SETTING',
        user=None,
        value=None
    )


def test_settings_use_cache(settings, mocker):
    settings.registry.register(
        'AWX_VAR',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )
    settings.cache.set('AWX_VAR', 'foobar')
    settings.cache.set('_awx_conf_preload_expires', 100)
    # Will fail test if database is used
    getattr(settings, 'AWX_VAR')


def test_settings_use_an_encrypted_cache(settings, mocker):
    settings.registry.register(
        'AWX_ENCRYPTED',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        encrypted=True
    )
    assert isinstance(settings.cache, EncryptedCacheProxy)
    assert settings.cache.__dict__['encrypter'] == encrypt_field
    assert settings.cache.__dict__['decrypter'] == decrypt_field
    settings.cache.set('AWX_ENCRYPTED_ID', 402)
    settings.cache.set('AWX_ENCRYPTED', 'foobar')
    settings.cache.set('_awx_conf_preload_expires', 100)
    # Will fail test if database is used
    getattr(settings, 'AWX_ENCRYPTED')


def test_sensitive_cache_data_is_encrypted(settings, mocker):
    "fields marked as `encrypted` are stored in the cache with encryption"
    settings.registry.register(
        'AWX_ENCRYPTED',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        encrypted=True
    )

    def rot13(obj, attribute):
        assert obj.pk == 123
        return codecs.encode(getattr(obj, attribute), 'rot_13')

    native_cache = LocMemCache(str(uuid4()), {})
    cache = EncryptedCacheProxy(
        native_cache,
        settings.registry,
        encrypter=rot13,
        decrypter=rot13
    )
    # Insert the setting value into the database; the encryption process will
    # use its primary key as part of the encryption key
    setting_from_db = mocker.Mock(pk=123, key='AWX_ENCRYPTED', value='SECRET!')
    mocks = mocker.Mock(**{
        'order_by.return_value': mocker.Mock(**{
            '__iter__': lambda self: iter([setting_from_db]),
            'first.return_value': setting_from_db
        }),
    })
    with mocker.patch('awx.conf.models.Setting.objects.filter', return_value=mocks):
        cache.set('AWX_ENCRYPTED', 'SECRET!')
        assert cache.get('AWX_ENCRYPTED') == 'SECRET!'
        assert native_cache.get('AWX_ENCRYPTED') == 'FRPERG!'


def test_readonly_sensitive_cache_data_is_encrypted(settings):
    "readonly fields marked as `encrypted` are stored in the cache with encryption"
    settings.registry.register(
        'AWX_ENCRYPTED',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system',
        read_only=True,
        encrypted=True
    )

    def rot13(obj, attribute):
        assert obj.pk is None
        return codecs.encode(getattr(obj, attribute), 'rot_13')

    native_cache = LocMemCache(str(uuid4()), {})
    cache = EncryptedCacheProxy(
        native_cache,
        settings.registry,
        encrypter=rot13,
        decrypter=rot13
    )
    cache.set('AWX_ENCRYPTED', 'SECRET!')
    assert cache.get('AWX_ENCRYPTED') == 'SECRET!'
    assert native_cache.get('AWX_ENCRYPTED') == 'FRPERG!'
