# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger('awx.conf.settings')

__all__ = ['clear_old_license']    
    

def clear_old_license(apps, schema_editor):
    Setting = apps.get_model('conf', 'Setting')
    Setting.objects.filter(key='LICENSE').delete()
