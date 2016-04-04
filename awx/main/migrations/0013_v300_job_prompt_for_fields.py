# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_v300_create_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_limit_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_inventory_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_job_type_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_tags_on_launch',
            field=models.BooleanField(default=False),
        ),
    ]
