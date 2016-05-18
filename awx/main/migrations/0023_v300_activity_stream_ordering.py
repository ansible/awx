# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_v300_adhoc_extravars'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activitystream',
            options={'ordering': ('pk',)},
        ),
    ]
