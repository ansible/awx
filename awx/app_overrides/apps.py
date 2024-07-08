from django.apps import AppConfig


class AppOverridesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'awx.app_overrides'
    label = 'app_overrides'
