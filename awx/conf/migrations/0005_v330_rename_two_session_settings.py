# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils import timezone
from django.db import migrations


def copy_session_settings(apps, schema_editor):

    
    def rename_setting(old_key, new_key):
        Setting = apps.get_model('conf', 'Setting')
        
        if Setting.objects.filter(key=new_key).exists():
            logger.error('Setting', new_key, 'unexpectedly exists before this migration, \
                          it will be replaced by the value of the', AUTH_TOKEN_EXPIRATION, 'setting.')
            
    
    
    
    Setting = apps.get_model('conf', 'Setting')
    
    mapping = {
    'AUTH_TOKEN_EXPIRATION': 'SESSION_COOKIE_AGE',
    'AUTH_TOKEN_PER_USER': 'SESSIONS_PER_USER'
}
for before, after in mapping.items():
    ...
    
    
    for setting_name in mapping:
        old_setting = Setting.objects.filter(key=setting_name).first()
        if 
    
    if Setting.objects.filter(key='SESSION_COOKIE_AGE').exists():
        logger.error('Setting SESSION_COOKIE_AGE unexpectedly exists before this migration, it will be replaced by AUTH_TOKEN_EXPIRATION setting')
    
    
    if Setting.objects.filter(key='AUTH_TOKEN_EXPIRATION').exists():
        Setting.objects.filter(key='SESSION_COOKIE_AGE').delete()
        Setting.objects.get_or_create(key='SESSION_COOKIE_AGE', 
                                      value=Setting.objects.get(key='AUTH_TOKEN_EXPIRATION').value,
                                      created=timezone.now(),
                                      modified=timezone.now())
                                      
    if Setting.objects.filter(key='AUTH_TOKEN_PER_USER').exists():
        Setting.objects.filter(key='SESSIONS_PER_USER').delete()
        Setting.objects.get_or_create(key='SESSIONS_PER_USER', 
                                      value=Setting.objects.get(key='AUTH_TOKEN_PER_USER').value,
                                      created=timezone.now(),
                                      modified=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0004_v320_reencrypt'),
    ]

    operations = [
        migrations.RunPython(copy_session_settings),
    ]
    