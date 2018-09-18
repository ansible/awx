# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.utils.timezone import now
from django.conf import settings

logger = logging.getLogger('awx.conf.settings')

__all__ = ['rename_setting']    
    
    
def rename_setting(apps, schema_editor, old_key, new_key):
    
    old_setting = None
    Setting = apps.get_model('conf', 'Setting')
    if Setting.objects.filter(key=new_key).exists() or hasattr(settings, new_key):
        logger.info('Setting ' + new_key + ' unexpectedly exists before this migration, it will be replaced by the value of the ' + old_key + ' setting.')
        Setting.objects.filter(key=new_key).delete()
    # Look for db setting, which wouldn't be picked up by SettingsWrapper because the register method is gone
    if Setting.objects.filter(key=old_key).exists():
        old_setting = Setting.objects.filter(key=old_key).last().value
        Setting.objects.filter(key=old_key).delete()
    # Look for "on-disk" setting (/etc/tower/conf.d)
    if hasattr(settings, old_key):
        old_setting = getattr(settings, old_key)
    if old_setting is not None:
        Setting.objects.create(key=new_key, 
                               value=old_setting, 
                               created=now(),
                               modified=now()
                               )
        
