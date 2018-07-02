# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

logger = logging.getLogger('awx.conf.settings')

__all__ = ['rename_setting']    
    
    
def rename_setting(apps, schema_editor, old_key, new_key):

    Setting = apps.get_model('conf', 'Setting')

    if Setting.objects.filter(key=new_key).exists():
        logger.error('Setting', new_key, 'unexpectedly exists before this migration, \
                      it will be replaced by the value of the', old_key, 'setting.')
        Setting.objects.filter(key=new_key).delete()
        
    old_setting = Setting.objects.filter(key=old_key).first()
    if old_setting is not None:
        Setting.objects.create(key=new_key, value=old_setting.value)
        Setting.objects.filter(key=old_key).delete()
        
def reverse_rename_setting(apps, schema_editor, old_key, new_key):

    Setting = apps.get_model('conf', 'Setting')

    if Setting.objects.filter(key=old_key).exists():
        logger.error('Setting', old_key, 'unexpectedly exists before this migration, \
                      it will be replaced by the value of the', new_key, 'setting.')
        Setting.objects.filter(key=old_key).delete()
        
    new_setting = Setting.objects.filter(key=new_key).first()
    if new_setting is not None:
        Setting.objects.create(key=old_key, value=new_setting.value)
        Setting.objects.filter(key=new_key).delete()
        