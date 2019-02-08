# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0060_v350_update_schedule_uniqueness_constraint'),
    ]

    operations = [
        migrations.RunPython(credentialtypes.add_openstack_verify_field),
    ]
