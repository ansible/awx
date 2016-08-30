# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0033_v301_workflow_create'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflownode',
            name='job',
            field=models.ForeignKey(related_name='workflow_job_nodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJob', null=True),
        ),
    ]
