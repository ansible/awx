# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0049_v310_workflow_surveys'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unifiedjob',
            name='launch_type',
            field=models.CharField(default=b'manual', max_length=20, editable=False, choices=[(b'manual', 'Manual'), (b'relaunch', 'Relaunch'), (b'callback', 'Callback'), (b'scheduled', 'Scheduled'), (b'dependency', 'Dependency'), (b'workflow', 'Workflow')]),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='job',
            field=models.OneToOneField(related_name='unified_job_node', null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJob'),
        ),
    ]
