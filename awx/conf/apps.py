# Django
from django.apps import AppConfig
# from django.core import checks
from django.utils.translation import ugettext_lazy as _
from awx.main.utils.handlers import configure_external_logger
from django.conf import settings


class ConfConfig(AppConfig):

    name = 'awx.conf'
    verbose_name = _('Configuration')

    def configure_oauth2_provider(self, settings):
        from oauth2_provider import settings as o_settings
        o_settings.oauth2_settings = o_settings.OAuth2ProviderSettings(
            settings.OAUTH2_PROVIDER, o_settings.DEFAULTS,
            o_settings.IMPORT_STRINGS, o_settings.MANDATORY
        )

    def ready(self):
        self.module.autodiscover()
        from .settings import SettingsWrapper
        SettingsWrapper.initialize()
        configure_external_logger(settings)
        self.configure_oauth2_provider(settings)
