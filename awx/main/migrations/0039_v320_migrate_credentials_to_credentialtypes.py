# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import taggit.managers
import awx.main.fields
from awx.main.migrations import _credentialtypes as credentialtypes


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_v320_data_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='CredentialType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default=b'', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('kind', models.CharField(max_length=32, choices=[(b'machine', 'Machine'), (b'net', 'Network'), (b'scm', 'Source Control'), (b'cloud', 'Cloud')])),
                ('managed_by_tower', models.BooleanField(default=False, editable=False)),
                ('inputs', awx.main.fields.CredentialTypeInputField(default={}, blank=True)),
                ('injectors', awx.main.fields.CredentialTypeInjectorField(default={}, blank=True)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'credentialtype', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'credentialtype', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ('kind', 'name'),
            },
        ),
        migrations.AlterModelOptions(
            name='credential',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='credential',
            name='inputs',
            field=awx.main.fields.CredentialInputField(default={}, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='credential_type',
            field=models.ForeignKey(related_name='credentials', to='main.CredentialType', null=True),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([('organization', 'name', 'credential_type')]),
        ),
        migrations.RunPython(credentialtypes.create_tower_managed_credential_types),
        # MIGRATION TODO: For each credential, look at the columns below to
        # determine the appropriate CredentialType (and assign it).  Additionally,
        # set `self.input` to the appropriate JSON blob
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
        # MIGRATION TODO: Once credentials are migrated, alter the credential_type
        # foreign key to be non-NULLable
    ]
