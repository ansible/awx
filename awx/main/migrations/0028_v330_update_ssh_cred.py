# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_v330_add_tower_verify'),
    ]

    operations = [
        migrations.RunPython(credentialtypes.add_become_field),
    ]
