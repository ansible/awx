# Django
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SSOConfig(AppConfig):

    name = 'awx.sso'
    verbose_name = _('Single Sign-On')
