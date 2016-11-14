# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0049_v310_workflow_surveys'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adhoccommandevent',
            name='event_data',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='artifacts',
            field=awx.main.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='survey_passwords',
            field=awx.main.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='event_data',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='survey_spec',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='body',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='notification_configuration',
            field=awx.main.fields.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='project',
            name='playbook_files',
            field=awx.main.fields.JSONField(default=[], help_text='List of playbooks found in the project', verbose_name='Playbook Files', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='extra_data',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='job_env',
            field=awx.main.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjob',
            name='survey_passwords',
            field=awx.main.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='ancestor_artifacts',
            field=awx.main.fields.JSONField(default={}, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='char_prompts',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplate',
            name='survey_spec',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplatenode',
            name='char_prompts',
            field=awx.main.fields.JSONField(default={}, blank=True),
        ),
    ]
