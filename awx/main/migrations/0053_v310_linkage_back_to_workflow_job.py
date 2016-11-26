# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0052_v310_inventory_name_non_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='unifiedjob',
            name='source_workflow_job',
            field=models.ForeignKey(related_name='spawned_jobs', on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to='main.WorkflowJob', null=True),
        ),
    ]
