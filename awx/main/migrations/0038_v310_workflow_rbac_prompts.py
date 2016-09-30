# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import django.db.models.deletion
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_v310_remove_tower_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowjobnode',
            name='char_prompts',
            field=jsonfield.fields.JSONField(default={}, blank=True),
        ),
        migrations.AddField(
            model_name='workflowjobnode',
            name='credential',
            field=models.ForeignKey(related_name='workflowjobnodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='workflowjobnode',
            name='inventory',
            field=models.ForeignKey(related_name='workflowjobnodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Inventory', null=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='execute_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='organization',
            field=models.ForeignKey(related_name='workflows', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='main.Organization', null=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'organization.auditor_role', b'execute_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AddField(
            model_name='workflowjobtemplatenode',
            name='char_prompts',
            field=jsonfield.fields.JSONField(default={}, blank=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplatenode',
            name='credential',
            field=models.ForeignKey(related_name='workflowjobtemplatenodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplatenode',
            name='inventory',
            field=models.ForeignKey(related_name='workflowjobtemplatenodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Inventory', null=True),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='unified_job_template',
            field=models.ForeignKey(related_name='workflowjobnodes', on_delete=django.db.models.deletion.SET_NULL, default=None, to='main.UnifiedJobTemplate', null=True),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='workflow_job',
            field=models.ForeignKey(related_name='workflow_job_nodes', default=None, blank=True, to='main.WorkflowJob', null=True),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplate',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_administrator', b'organization.admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplatenode',
            name='unified_job_template',
            field=models.ForeignKey(related_name='workflowjobtemplatenodes', on_delete=django.db.models.deletion.SET_NULL, default=None, to='main.UnifiedJobTemplate', null=True),
        ),
    ]
