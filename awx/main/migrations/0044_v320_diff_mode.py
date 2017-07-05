# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0043_v320_instancegroups'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='diff_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='diff_mode',
            field=models.BooleanField(default=False),
        ),
    ]
