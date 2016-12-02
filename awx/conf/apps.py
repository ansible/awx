# Django
from django.apps import AppConfig
# from django.core import checks
from django.utils.translation import ugettext_lazy as _
from django.utils.log import configure_logging
from django.conf import settings


class ConfConfig(AppConfig):

    name = 'awx.conf'
    verbose_name = _('Configuration')

    def ready(self):
        self.module.autodiscover()
        from .settings import SettingsWrapper
        SettingsWrapper.initialize()
        if settings.LOG_AGGREGATOR_ENABLED:
            LOGGING = settings.LOGGING
            LOGGING['handlers']['http_receiver']['class'] = 'awx.main.utils.handlers.HTTPSHandler'
            configure_logging(settings.LOGGING_CONFIG, LOGGING)
        # checks.register(SettingsWrapper._check_settings)
