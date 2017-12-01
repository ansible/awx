# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from awx.main.migrations import _migration_utils as migration_utils
from awx.main.migrations import _credentialtypes as credentialtypes
from awx.main.migrations._multi_cred import migrate_to_multi_cred


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='unifiedjob',
            name='credentials',
            field=models.ManyToManyField(related_name='unifiedjobs', to='main.Credential'),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='credentials',
            field=models.ManyToManyField(related_name='unifiedjobtemplates', to='main.Credential'),
        ),
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(migrate_to_multi_cred),
        migrations.RemoveField(
            model_name='job',
            name='credential',
        ),
        migrations.RemoveField(
            model_name='job',
            name='extra_credentials',
        ),
        migrations.RemoveField(
            model_name='job',
            name='vault_credential',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='credential',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='extra_credentials',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='vault_credential',
        ),
        migrations.RunPython(credentialtypes.add_vault_id_field)
    ]
