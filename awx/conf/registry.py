# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
from collections import OrderedDict
import logging

# Django
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from awx.conf.license import get_license

logger = logging.getLogger('awx.conf.registry')

__all__ = ['settings_registry']


class SettingsRegistry(object):
    """Registry of all API-configurable settings and categories."""

    def __init__(self, settings=None):
        """
        :param settings: a ``django.conf.LazySettings`` object used to lookup
                         file-based field values (e.g., ``local_settings.py``
                         and ``/etc/tower/conf.d/example.py``).  If unspecified,
                         defaults to ``django.conf.settings``.
        """
        if settings is None:
            from django.conf import settings
        self._registry = OrderedDict()
        self._validate_registry = {}
        self._dependent_settings = {}
        self.settings = settings

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

    def register_validate(self, category_slug, func):
        self._validate_registry[category_slug] = func

    def unregister_validate(self, category_slug):
        self._validate_registry.pop(category_slug, None)

    def get_dependent_settings(self, setting):
        return self._dependent_settings.get(setting, set())

    def get_registered_categories(self):
        categories = {
            'all': _('All'),
            'changed': _('Changed'),
        }
        for setting, kwargs in self._registry.items():
            category_slug = kwargs.get('category_slug', None)
            if category_slug is None or category_slug in categories:
                continue
            if category_slug == 'user':
                categories['user'] = _('User')
                categories['user-defaults'] = _('User-Defaults')
            else:
                categories[category_slug] = kwargs.get('category', None) or category_slug
        return categories

    def get_registered_settings(self, category_slug=None, read_only=None, slugs_to_ignore=set()):
        setting_names = []
        if category_slug == 'user-defaults':
            category_slug = 'user'
        if category_slug == 'changed':
            category_slug = 'all'
        for setting, kwargs in self._registry.items():
            if category_slug not in {None, 'all', kwargs.get('category_slug', None)}:
                continue
            if kwargs.get('category_slug', None) in slugs_to_ignore:
                continue
            if (read_only in {True, False} and kwargs.get('read_only', False) != read_only and
                    setting not in ('INSTALL_UUID', 'AWX_ISOLATED_PRIVATE_KEY', 'AWX_ISOLATED_PUBLIC_KEY')):
                # Note: Doesn't catch fields that set read_only via __init__;
                # read-only field kwargs should always include read_only=True.
                continue
            setting_names.append(setting)
        return setting_names

    def get_registered_validate_func(self, category_slug):
        return self._validate_registry.get(category_slug, None)

    def is_setting_encrypted(self, setting):
        return bool(self._registry.get(setting, {}).get('encrypted', False))

    def is_setting_read_only(self, setting):
        return bool(self._registry.get(setting, {}).get('read_only', False))

    def get_setting_category(self, setting):
        return self._registry.get(setting, {}).get('category_slug', None)

    def get_setting_field(self, setting, mixin_class=None, for_user=False, **kwargs):
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
        encrypted = bool(field_kwargs.pop('encrypted', False))
        defined_in_file = bool(field_kwargs.pop('defined_in_file', False))
        unit = field_kwargs.pop('unit', None)
        if getattr(field_kwargs.get('child', None), 'source', None) is not None:
            field_kwargs['child'].source = None
        field_instance = field_class(**field_kwargs)
        field_instance.category_slug = category_slug
        field_instance.category = category
        field_instance.depends_on = depends_on
        field_instance.unit = unit
        if placeholder is not empty:
            field_instance.placeholder = placeholder
        field_instance.defined_in_file = defined_in_file
        if field_instance.defined_in_file:
            field_instance.help_text = (
                str(_('This value has been set manually in a settings file.')) +
                '\n\n' +
                str(field_instance.help_text)
            )
        field_instance.encrypted = encrypted
        original_field_instance = field_instance
        if field_class != original_field_class:
            original_field_instance = original_field_class(**field_kwargs)
        if category_slug == 'user' and for_user:
            try:
                field_instance.default = original_field_instance.to_representation(getattr(self.settings, setting))
            except Exception:
                logger.warning('Unable to retrieve default value for user setting "%s".', setting, exc_info=True)
        elif not field_instance.read_only or field_instance.default is empty or field_instance.defined_in_file:
            try:
                field_instance.default = original_field_instance.to_representation(self.settings._awx_conf_settings._get_default(setting))
            except AttributeError:
                pass
            except Exception:
                logger.warning('Unable to retrieve default value for setting "%s".', setting, exc_info=True)

        # `PENDO_TRACKING_STATE` is disabled for the open source awx license
        if setting == 'PENDO_TRACKING_STATE' and get_license().get('license_type') == 'open':
            field_instance.read_only = True

        return field_instance


settings_registry = SettingsRegistry()
