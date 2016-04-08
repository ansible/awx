# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_v300_label_changes'),
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
        migrations.AlterField(
            model_name='job',
            name='inventory',
            field=models.ForeignKey(related_name='jobs', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Inventory', null=True),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='inventory',
            field=models.ForeignKey(related_name='jobtemplates', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Inventory', null=True),
        ),
    ]
