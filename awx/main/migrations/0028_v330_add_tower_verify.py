# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_v330_emitted_events'),
    ]

    operations = [
        migrations.RunPython(credentialtypes.add_tower_verify_field),
    ]
