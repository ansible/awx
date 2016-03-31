# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0011_v300_credential_domain_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default=b'', blank=True)),
                ('name', models.CharField(max_length=512)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'label', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'label', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('organization', models.ForeignKey(related_name='labels', to='main.Organization', help_text='Organization this label belongs to.')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ('organization', 'name'),
            },
        ),
        migrations.AddField(
            model_name='activitystream',
            name='label',
            field=models.ManyToManyField(to='main.Label', blank=True),
        ),
        migrations.AddField(
            model_name='job',
            name='labels',
            field=models.ManyToManyField(related_name='job_labels', to='main.Label', blank=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='labels',
            field=models.ManyToManyField(related_name='jobtemplate_labels', to='main.Label', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='label',
            unique_together=set([('name', 'organization')]),
        ),
    ]
