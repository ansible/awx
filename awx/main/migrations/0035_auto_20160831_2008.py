# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0034_auto_20160830_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workflownode',
            name='workflow_job_template',
            field=models.ForeignKey(related_name='workflow_nodes', default=None, blank=True, to='main.WorkflowJobTemplate', null=True),
        ),
    ]
