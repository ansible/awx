# Django
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UINextConfig(AppConfig):

    name = 'awx.ui_next'
    verbose_name = _('UI_Next')

