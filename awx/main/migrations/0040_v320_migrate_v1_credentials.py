# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from awx.main.migrations import _credentialtypes as credentialtypes


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0039_v320_add_credentialtype_model'),
    ]

    operations = [
        migrations.RunPython(credentialtypes.migrate_to_v2_credentials),
    ]
