# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0041_v310_artifacts'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorysource',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='inventoryupdate',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='job',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='projectupdate',
            name='timeout',
            field=models.PositiveIntegerField(default=0, blank=True),
        ),
    ]
