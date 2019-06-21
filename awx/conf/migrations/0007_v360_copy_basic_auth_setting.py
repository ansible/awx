# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
from awx.conf.migrations import _rename_setting
    
    
def copy_basic_auth_setting(apps, schema_editor):
    _rename_setting.copy_setting(apps, schema_editor, old_key='AUTH_BASIC_ENABLED')


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0006_v331_ldap_group_type'),
    ]

    operations = [
        migrations.RunPython(copy_basic_auth_setting, None),
    ]
    