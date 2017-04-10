# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_v311_insights'),
    ]

    operations = [
        migrations.AddField(
            model_name='instance',
            name='version',
            field=models.CharField(max_length=24, blank=True),
        ),
    ]
