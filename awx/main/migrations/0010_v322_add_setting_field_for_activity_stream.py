# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_v322_add_support_for_ovirt4_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitystream',
            name='setting',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
    ]
