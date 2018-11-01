# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.conf.migrations._ldap_group_type import fill_ldap_group_type_params

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0005_v330_rename_two_session_settings'),
    ]

    operations = [
        migrations.RunPython(fill_ldap_group_type_params),
    ]
