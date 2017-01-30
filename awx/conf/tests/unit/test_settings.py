# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from contextlib import contextmanager
from uuid import uuid4
import time

from django.conf import LazySettings
from django.core.cache.backends.locmem import LocMemCache
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from rest_framework import fields
import pytest

from awx.conf import models
from awx.conf.settings import SettingsWrapper, SETTING_CACHE_NOTSET
from awx.conf.registry import SettingsRegistry


@contextmanager
def apply_patches(_patches):
    [p.start() for p in _patches]
    yield
    [p.stop() for p in _patches]


@pytest.fixture()
def settings(request):
    cache = LocMemCache(str(uuid4()), {})  # make a new random cache each time
    settings = LazySettings()
    registry = SettingsRegistry(settings)

    # @pytest.mark.readonly can be used to mark specific setting values as
    # "read-only".  This is analogous to manually specifying a setting on the
    # filesystem (e.g., in a local_settings.py in development, or in
    # /etc/tower/conf.d/<something>.py)
    readonly_marker = request.node.get_marker('readonly')
    defaults = readonly_marker.kwargs if readonly_marker else {}
    defaults['DEFAULTS_SNAPSHOT'] = {}
    settings.configure(**defaults)
    settings._wrapped = SettingsWrapper(settings._wrapped,
                                        cache,
                                        registry)
    return settings


@pytest.mark.readonly(DEBUG=True)
def test_unregistered_setting(settings):
    "native Django settings are not stored in DB, and aren't cached"
    assert settings.DEBUG is True
    assert settings.cache.get('DEBUG') is None


@pytest.mark.readonly(AWX_SOME_SETTING='DEFAULT')
def test_read_only_setting(settings):
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )
    assert settings.AWX_SOME_SETTING == 'DEFAULT'
    assert len(settings.registry.get_registered_settings(read_only=False)) == 0
    settings = settings.registry.get_registered_settings(read_only=True)
    assert settings == ['AWX_SOME_SETTING']


@pytest.mark.readonly(AWX_SOME_SETTING='DEFAULT')
def test_read_only_setting_with_empty_default(settings):
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


@pytest.mark.readonly(AWX_SOME_SETTING='DEFAULT')
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


@pytest.mark.readonly(AWX_SOME_SETTING='DEFAULT')
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


def test_empty_setting(settings, mocker):
    "settings with no default and no defined value are not valid"
    settings.registry.register(
        'AWX_SOME_SETTING',
        field_class=fields.CharField,
        category=_('System'),
        category_slug='system'
    )

    settings_to_cache = [
        mocker.Mock(**{'order_by.return_value': []}),
        mocker.Mock(**{'order_by.return_value.first.return_value': None})
    ]
    with mocker.patch('awx.conf.models.Setting.objects.filter', side_effect=settings_to_cache):
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

    settings_to_cache = [
        mocker.Mock(**{'order_by.return_value': [
            mocker.Mock(key='AWX_SOME_SETTING', value='FROM_DB')
        ]}),
    ]
    with mocker.patch('awx.conf.models.Setting.objects.filter', side_effect=settings_to_cache):
        assert settings.AWX_SOME_SETTING == 'FROM_DB'
        assert settings.cache.get('AWX_SOME_SETTING') == 'FROM_DB'


@pytest.mark.readonly(AWX_SOME_SETTING='DEFAULT')
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


@pytest.mark.readonly(AWX_SOME_SETTING='DEFAULT')
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
