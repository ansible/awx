# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations
from django.db import models
# AWX
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_v320_data_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='credential',
            name='authorize',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='authorize_password',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='become_method',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='become_password',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='become_username',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='client',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='cloud',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='host',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='kind',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='password',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='project',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='secret',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='security_token',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='ssh_key_data',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='ssh_key_unlock',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='subscription',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='tenant',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='username',
        ),
        migrations.RemoveField(
            model_name='credential',
            name='vault_password',
        ),
        migrations.AlterUniqueTogether(
            name='credentialtype',
            unique_together=set([('name', 'kind')]),
        ),
        migrations.AlterField(
            model_name='credential',
            name='credential_type',
            field=models.ForeignKey(related_name='credentials', to='main.CredentialType', on_delete=models.CASCADE, null=False, help_text='Specify the type of credential you want to create. Refer to the Ansible Tower documentation for details on each type.')
        ),
        migrations.AlterField(
            model_name='credential',
            name='inputs',
            field=awx.main.fields.CredentialInputField(default=dict, help_text='Enter inputs using either JSON or YAML syntax. Use the radio button to toggle between the two. Refer to the Ansible Tower documentation for example syntax.', blank=True),
        ),
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
