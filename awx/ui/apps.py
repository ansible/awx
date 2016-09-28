# Django
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UIConfig(AppConfig):

    name = 'awx.ui'
    verbose_name = _('UI')
