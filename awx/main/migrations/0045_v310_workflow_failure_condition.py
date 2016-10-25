# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0040_v310_artifacts'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowjobnode',
            name='fail_on_job_failure',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplatenode',
            name='fail_on_job_failure',
            field=models.BooleanField(default=True),
        ),
    ]
