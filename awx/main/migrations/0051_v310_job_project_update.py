# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_v310_JSONField_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='project_update',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.ProjectUpdate', help_text='The SCM Refresh task used to make sure the playbooks were available for the job run', null=True),
        ),
    ]
