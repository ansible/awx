# Django
from django.apps import AppConfig
# from django.core import checks
from django.utils.translation import ugettext_lazy as _
from awx.main.utils.handlers import configure_external_logger
from django.conf import settings


class ConfConfig(AppConfig):

    name = 'awx.conf'
    verbose_name = _('Configuration')

    def ready(self):
        self.module.autodiscover()
        from .settings import SettingsWrapper
        SettingsWrapper.initialize()
        configure_external_logger(settings)
