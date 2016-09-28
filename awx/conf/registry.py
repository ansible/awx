# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
from collections import OrderedDict
import logging

# Django
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger('awx.conf.registry')

__all__ = ['settings_registry']


class SettingsRegistry(object):
    """Registry of all API-configurable settings and categories."""

    def __init__(self):
        self._registry = OrderedDict()
        self._dependent_settings = {}

    def register(self, setting, **kwargs):
        if setting in self._registry:
            raise ImproperlyConfigured('Setting "{}" is already registered.'.format(setting))
        category = kwargs.setdefault('category', None)
        category_slug = kwargs.setdefault('category_slug', slugify(category or '') or None)
        if category_slug in {'all', 'changed', 'user-defaults'}:
            raise ImproperlyConfigured('"{}" is a reserved category slug.'.format(category_slug))
        if 'field_class' not in kwargs:
            raise ImproperlyConfigured('Setting must provide a field_class keyword argument.')
        self._registry[setting] = kwargs

        # Normally for read-only/dynamic settings, depends_on will specify other
        # settings whose changes may affect the value of this setting. Store
        # this setting as a dependent for the other settings, so we can know
        # which extra cache keys to clear when a setting changes.
        depends_on = kwargs.setdefault('depends_on', None) or set()
        for depends_on_setting in depends_on:
            dependent_settings = self._dependent_settings.setdefault(depends_on_setting, set())
            dependent_settings.add(setting)

    def unregister(self, setting):
        self._registry.pop(setting, None)
        for dependent_settings in self._dependent_settings.values():
            dependent_settings.discard(setting)

    def get_dependent_settings(self, setting):
        return self._dependent_settings.get(setting, set())

    def get_registered_categories(self):
        categories = {
            'all': _('All'),
            'changed': _('Changed'),
            'user': _('User'),
            'user-defaults': _('User Defaults'),
        }
        for setting, kwargs in self._registry.items():
            category_slug = kwargs.get('category_slug', None)
            if category_slug is None or category_slug in categories:
                continue
            categories[category_slug] = kwargs.get('category', None) or category_slug
        return categories

    def get_registered_settings(self, category_slug=None, read_only=None):
        setting_names = []
        if category_slug == 'user-defaults':
            category_slug = 'user'
        if category_slug == 'changed':
            category_slug = 'all'
        for setting, kwargs in self._registry.items():
            if category_slug not in {None, 'all', kwargs.get('category_slug', None)}:
                continue
            if read_only in {True, False} and kwargs.get('read_only', False) != read_only:
                # Note: Doesn't catch fields that set read_only via __init__;
                # read-only field kwargs should always include read_only=True.
                continue
            setting_names.append(setting)
        return setting_names

    def get_setting_field(self, setting, mixin_class=None, for_user=False, **kwargs):
        from django.conf import settings
        from rest_framework.fields import empty
        field_kwargs = {}
        field_kwargs.update(self._registry[setting])
        field_kwargs.update(kwargs)
        field_class = original_field_class = field_kwargs.pop('field_class')
        if mixin_class:
            field_class = type(field_class.__name__, (mixin_class, field_class), {})
        category_slug = field_kwargs.pop('category_slug', None)
        category = field_kwargs.pop('category', None)
        depends_on = frozenset(field_kwargs.pop('depends_on', None) or [])
        placeholder = field_kwargs.pop('placeholder', empty)
        if getattr(field_kwargs.get('child', None), 'source', None) is not None:
            field_kwargs['child'].source = None
        field_instance = field_class(**field_kwargs)
        field_instance.category_slug = category_slug
        field_instance.category = category
        field_instance.depends_on = depends_on
        if placeholder is not empty:
            field_instance.placeholder = placeholder
        original_field_instance = field_instance
        if field_class != original_field_class:
            original_field_instance = original_field_class(**field_kwargs)
        if category_slug == 'user' and for_user:
            try:
                field_instance.default = original_field_instance.to_representation(getattr(settings, setting))
            except:
                logger.warning('Unable to retrieve default value for user setting "%s".', setting, exc_info=True)
        elif not field_instance.read_only or field_instance.default is empty:
            try:
                field_instance.default = original_field_instance.to_representation(settings._awx_conf_settings._get_default(setting))
            except AttributeError:
                pass
            except:
                logger.warning('Unable to retrieve default value for setting "%s".', setting, exc_info=True)
        return field_instance

settings_registry = SettingsRegistry()
