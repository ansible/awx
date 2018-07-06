# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
from awx.conf.migrations import _rename_setting
    
    
def copy_session_settings(apps, schema_editor):
    _rename_setting.rename_setting(apps, schema_editor, old_key='AUTH_TOKEN_PER_USER', new_key='SESSIONS_PER_USER')
    _rename_setting.rename_setting(apps, schema_editor, old_key='AUTH_TOKEN_EXPIRATION', new_key='SESSION_COOKIE_AGE')


def reverse_copy_session_settings(apps, schema_editor):
    _rename_setting.rename_setting(apps, schema_editor, old_key='SESSION_COOKIE_AGE', new_key='AUTH_TOKEN_EXPIRATION')
    _rename_setting.rename_setting(apps, schema_editor, old_key='SESSIONS_PER_USER', new_key='AUTH_TOKEN_PER_USER')


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0004_v320_reencrypt'),
    ]

    operations = [
        migrations.RunPython(copy_session_settings, reverse_copy_session_settings),
    ]
    