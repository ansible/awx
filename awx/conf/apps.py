import sys

# Django
from django.apps import AppConfig

# from django.core import checks
from django.utils.translation import gettext_lazy as _


class ConfConfig(AppConfig):
    name = 'awx.conf'
    verbose_name = _('Configuration')

    def ready(self):
        self.module.autodiscover()

        if not set(sys.argv) & {'migrate', 'check_migrations', 'showmigrations'}:
            from .settings import SettingsWrapper

            SettingsWrapper.initialize()
