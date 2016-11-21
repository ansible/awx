# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0051_v310_job_project_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='name',
            field=models.CharField(max_length=512),
        ),
    ]
