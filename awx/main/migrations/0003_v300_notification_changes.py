# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0002_v300_tower_settings_changes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('status', models.CharField(default=b'pending', max_length=20, editable=False, choices=[(b'pending', 'Pending'), (b'successful', 'Successful'), (b'failed', 'Failed')])),
                ('error', models.TextField(default=b'', editable=False, blank=True)),
                ('notifications_sent', models.IntegerField(default=0, editable=False)),
                ('notification_type', models.CharField(max_length=32, choices=[(b'email', 'Email'), (b'slack', 'Slack'), (b'twilio', 'Twilio'), (b'pagerduty', 'Pagerduty'), (b'hipchat', 'HipChat'), (b'webhook', 'Webhook'), (b'irc', 'IRC')])),
                ('recipients', models.TextField(default=b'', editable=False, blank=True)),
                ('subject', models.TextField(default=b'', editable=False, blank=True)),
                ('body', jsonfield.fields.JSONField(default=dict, blank=True)),
            ],
            options={
                'ordering': ('pk',),
            },
        ),
        migrations.CreateModel(
            name='Notifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('description', models.TextField(default=b'', blank=True)),
                ('active', models.BooleanField(default=True, editable=False)),
                ('name', models.CharField(unique=True, max_length=512)),
                ('notification_type', models.CharField(max_length=32, choices=[(b'email', 'Email'), (b'slack', 'Slack'), (b'twilio', 'Twilio'), (b'pagerduty', 'Pagerduty'), (b'hipchat', 'HipChat'), (b'webhook', 'Webhook'), (b'irc', 'IRC')])),
                ('notification_configuration', jsonfield.fields.JSONField(default=dict)),
                ('created_by', models.ForeignKey(related_name="{u'class': 'notifier', u'app_label': 'main'}(class)s_created+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name="{u'class': 'notifier', u'app_label': 'main'}(class)s_modified+", on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
                ('organization', models.ForeignKey(related_name='notifiers', on_delete=django.db.models.deletion.SET_NULL, to='main.Organization', null=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
        ),
        migrations.AddField(
            model_name='notification',
            name='notifier',
            field=models.ForeignKey(related_name='notifications', editable=False, to='main.Notifier'),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='notification',
            field=models.ManyToManyField(to='main.Notification', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='notifier',
            field=models.ManyToManyField(to='main.Notifier', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='notifiers_any',
            field=models.ManyToManyField(related_name='organization_notifiers_for_any', to='main.Notifier', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='notifiers_error',
            field=models.ManyToManyField(related_name='organization_notifiers_for_errors', to='main.Notifier', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='notifiers_success',
            field=models.ManyToManyField(related_name='organization_notifiers_for_success', to='main.Notifier', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='notifications',
            field=models.ManyToManyField(related_name='unifiedjob_notifications', editable=False, to='main.Notification'),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='notifiers_any',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_notifiers_for_any', to='main.Notifier', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='notifiers_error',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_notifiers_for_errors', to='main.Notifier', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='notifiers_success',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_notifiers_for_success', to='main.Notifier', blank=True),
        ),
    ]
