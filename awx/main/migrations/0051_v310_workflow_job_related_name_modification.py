# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_v310_JSONField_changes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflowjob',
            name='workflow_job_template',
            field=models.ForeignKey(related_name='workflow_jobs', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.WorkflowJobTemplate', null=True),
        ),
    ]
