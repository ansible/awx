# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers

# AWX
import awx.main.fields
from awx.main.models import CredentialType
from awx.main.utils.common import set_current_apps


def setup_tower_managed_defaults(apps, schema_editor):
    set_current_apps(apps)
    CredentialType.setup_tower_managed_defaults()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
        ('main', '0066_v350_inventorysource_custom_virtualenv'),
    ]

    operations = [
        migrations.CreateModel(
            name='CredentialInputSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(blank=True, default='')),
                ('input_field_name', models.CharField(max_length=1024)),
                ('metadata', awx.main.fields.DynamicCredentialInputField(blank=True, default=dict)),
                ('created_by', models.ForeignKey(default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="{'class': 'credentialinputsource', 'model_name': 'credentialinputsource', 'app_label': 'main'}(class)s_created+", to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="{'class': 'credentialinputsource', 'model_name': 'credentialinputsource', 'app_label': 'main'}(class)s_modified+", to=settings.AUTH_USER_MODEL)),
                ('source_credential', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_input_sources', to='main.Credential')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
                ('target_credential', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='input_sources', to='main.Credential')),
            ],
        ),
        migrations.AlterField(
            model_name='credentialtype',
            name='kind',
            field=models.CharField(choices=[('ssh', 'Machine'), ('vault', 'Vault'), ('net', 'Network'), ('scm', 'Source Control'), ('cloud', 'Cloud'), ('insights', 'Insights'), ('external', 'External')], max_length=32),
        ),
        migrations.AlterUniqueTogether(
            name='credentialinputsource',
            unique_together=set([('target_credential', 'input_field_name')]),
        ),
        migrations.RunPython(setup_tower_managed_defaults),
    ]
