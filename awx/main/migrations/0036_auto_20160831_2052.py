# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0035_auto_20160831_2008'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflownode',
            name='workflow_job',
            field=models.ForeignKey(related_name='workflow_job_nodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.WorkflowJob', null=True),
        ),
        migrations.AlterField(
            model_name='workflownode',
            name='job',
            field=models.ForeignKey(related_name='unified_job_nodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJob', null=True),
        ),
    ]
