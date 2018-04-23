# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0035_v330_more_oauth2_help_text'),

    ]

    operations = [
        migrations.RunPython(credentialtypes.remove_become_methods),
    ]
