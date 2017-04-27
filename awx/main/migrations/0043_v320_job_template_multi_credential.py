# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from awx.main.migrations import _credentialtypes as credentialtypes
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0042_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='extra_credentials',
            field=models.ManyToManyField(related_name='_job_extra_credentials_+', to='main.Credential'),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='extra_credentials',
            field=models.ManyToManyField(related_name='_jobtemplate_extra_credentials_+', to='main.Credential'),
        ),
        migrations.RunPython(credentialtypes.migrate_job_credentials),
        migrations.RemoveField(
            model_name='job',
            name='cloud_credential',
        ),
        migrations.RemoveField(
            model_name='job',
            name='network_credential',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='cloud_credential',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='network_credential',
        ),
    ]
