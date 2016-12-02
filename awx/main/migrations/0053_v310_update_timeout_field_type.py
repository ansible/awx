# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0052_v310_inventory_name_non_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorysource',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
    ]
