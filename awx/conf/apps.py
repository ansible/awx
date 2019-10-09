# Django
from django.apps import AppConfig
# from django.core import checks
from django.utils.translation import ugettext_lazy as _


class ConfConfig(AppConfig):

    name = 'awx.conf'
    verbose_name = _('Configuration')

    # oauth2_settings grabs values from defaults.py, and does not get updated
    # with values set from tower (i.e. the UI), that is django.conf settings.
    # E.g. REFRESH_TOKEN_EXPIRE_SECONDS will retain the value in defaults.py, and
    # not the value set from the UI.
    # The following code resets the models and oauth2_validators imports to use
    # DynamicOAuth2ProviderSettings instead of OAuth2ProviderSettings.
    # This sub-class will check that the attribute first exists in django.conf.settings
    # and return that before using the oauth2_settings.
    
    def configure_oauth2_provider(self, settings):
        from django.conf import settings
        from oauth2_provider import settings as o_settings
        from oauth2_provider import models, oauth2_validators

        class DynamicOAuth2ProviderSettings(o_settings.OAuth2ProviderSettings):

            def __getattr__(self, attr):
                if attr in settings.OAUTH2_PROVIDER:
                    return settings.OAUTH2_PROVIDER[attr]
                return super(DynamicOAuth2ProviderSettings, self).__getattr__(attr)

        models.oauth2_settings = DynamicOAuth2ProviderSettings(
            models.oauth2_settings.user_settings, models.oauth2_settings.defaults,
            models.oauth2_settings.import_strings, models.oauth2_settings.mandatory
        )
        oauth2_validators.oauth2_settings = models.oauth2_settings


    def ready(self):
        self.module.autodiscover()
        from .settings import SettingsWrapper
        SettingsWrapper.initialize()
        from django.conf import settings
        self.configure_oauth2_provider(settings)
