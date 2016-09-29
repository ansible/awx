# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_v310_remove_tower_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='allow_simultaneous',
            field=models.BooleanField(default=False),
        ),
    ]
