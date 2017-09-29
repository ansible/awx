# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations, models
from django.conf import settings
import taggit.managers

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnsibleVersions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(default=b'', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('ansible_cmd', models.TextField()),
                ('ansible_playbook', models.TextField()),
                ('ansible_vault', models.TextField()),
                ('ansible_doc', models.TextField()),
                ('ansible_pull', models.TextField()),
                ('ansible_galaxy', models.TextField()),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'credentialtype', u'app_label': 'main'}(class)s_created+", on_delete=models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'credentialtype', u'app_label': 'main'}(class)s_modified+", on_delete=models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        # Add ansible version to template
        migrations.AddField(
            model_name='UnifiedJobTemplate',
            name='ansible_version',
            field=models.ForeignKey(on_delete=models.deletion.SET_NULL, to='main.AnsibleVersions', null=True),
        )
    ]

