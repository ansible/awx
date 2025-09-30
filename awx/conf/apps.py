# Django
from django.apps import AppConfig
from django.conf import settings as dj_settings
from django.core.cache import cache as django_cache

# from django.core import checks
from django.utils.translation import gettext_lazy as _


class ConfConfig(AppConfig):
    name = 'awx.conf'
    verbose_name = _('Configuration')

    def initialize_settings(self):
        from .lazy import settings
        from .settings import SettingsWrapper
        from .registry import settings_registry

        settings._wrapped = SettingsWrapper(default_settings=dj_settings, cache=django_cache, registry=settings_registry)
        settings_registry.apps_ready()

    def ready(self):
        self.module.autodiscover()
        self.initialize_settings()
