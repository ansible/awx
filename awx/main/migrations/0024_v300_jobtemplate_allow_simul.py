# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_v300_activity_stream_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtemplate',
            name='allow_simultaneous',
            field=models.BooleanField(default=False),
        ),
    ]
