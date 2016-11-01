# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0042_v310_job_timeout'),
    ]

    operations = [
        migrations.AddField(
            model_name='unifiedjob',
            name='execution_node',
            field=models.TextField(default=b'', editable=False, blank=True),
        ),
    ]
