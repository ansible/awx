# -*- coding: utf-8 -*-
import logging
from django.conf import settings

from awx.main.utils.licensing import Licenser

logger = logging.getLogger('awx.conf.settings')

__all__ = ['clear_old_license']    
    

def clear_old_license(apps, schema_editor):
    # Setting = apps.get_model('conf', 'Organization')
    # setting.objects.filter(key=LICENSE)
    licenser = Licenser()
    if licenser._check_product_cert():
        settings.LICENSE = licenser.UNLICENSED_DATA.copy()
