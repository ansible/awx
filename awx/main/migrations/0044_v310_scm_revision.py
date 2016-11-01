# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0043_v310_executionnode'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='scm_revision',
            field=models.CharField(default=b'', editable=False, max_length=1024, blank=True, help_text='The last revision fetched by a project update', verbose_name='SCM Revision'),
        ),
        migrations.AddField(
            model_name='projectupdate',
            name='job_type',
            field=models.CharField(default=b'check', max_length=64, choices=[(b'run', 'Run'), (b'check', 'Check')]),
        ),
        migrations.AddField(
            model_name='job',
            name='scm_revision',
            field=models.CharField(default=b'', editable=False, max_length=1024, blank=True, help_text='The SCM Revision from the Project used for this job, if available', verbose_name='SCM Revision'),
        ),

    ]
