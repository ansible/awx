# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.utils.timezone import now

logger = logging.getLogger('awx.conf.settings')

__all__ = ['rename_setting']    
    
    
def rename_setting(apps, schema_editor, old_key, new_key):

    Setting = apps.get_model('conf', 'Setting')

    if Setting.objects.filter(key=new_key).exists():
        logger.info('Setting ' + new_key + ' unexpectedly exists before this migration, it will be replaced by the value of the ' + old_key + ' setting.')
        Setting.objects.filter(key=new_key).delete()
        
    old_setting = Setting.objects.filter(key=old_key).first()
    if old_setting is not None:
        Setting.objects.create(key=new_key, 
                               value=old_setting.value, 
                               created=now(),
                               modified=now()
                               )
        Setting.objects.filter(key=old_key).delete()
        
        