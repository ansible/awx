# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import awx.main.models.notifications
import django.db.models.deletion
import awx.main.models.workflow
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_v302_credential_permissions_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowJob',
            fields=[
                ('unifiedjob_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='main.UnifiedJob')),
                ('extra_vars', models.TextField(default=b'', blank=True)),
            ],
            options={
                'ordering': ('id',),
            },
            bases=('main.unifiedjob', models.Model, awx.main.models.notifications.JobNotificationMixin, awx.main.models.workflow.WorkflowJobInheritNodesMixin),
        ),
        migrations.CreateModel(
            name='WorkflowJobNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('always_nodes', models.ManyToManyField(related_name='workflowjobnodes_always', to='main.WorkflowJobNode', blank=True)),
                ('failure_nodes', models.ManyToManyField(related_name='workflowjobnodes_failure', to='main.WorkflowJobNode', blank=True)),
                ('job', models.ForeignKey(related_name='unified_job_nodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJob', null=True)),
                ('success_nodes', models.ManyToManyField(related_name='workflowjobnodes_success', to='main.WorkflowJobNode', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkflowJobTemplate',
            fields=[
                ('unifiedjobtemplate_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='main.UnifiedJobTemplate')),
                ('extra_vars', models.TextField(default=b'', blank=True)),
                ('admin_role', awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'singleton:system_administrator', to='main.Role', null=b'True')),
            ],
            bases=('main.unifiedjobtemplate', models.Model),
        ),
        migrations.CreateModel(
            name='WorkflowJobTemplateNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('always_nodes', models.ManyToManyField(related_name='workflowjobtemplatenodes_always', to='main.WorkflowJobTemplateNode', blank=True)),
                ('failure_nodes', models.ManyToManyField(related_name='workflowjobtemplatenodes_failure', to='main.WorkflowJobTemplateNode', blank=True)),
                ('success_nodes', models.ManyToManyField(related_name='workflowjobtemplatenodes_success', to='main.WorkflowJobTemplateNode', blank=True)),
                ('unified_job_template', models.ForeignKey(related_name='workflowjobtemplatenodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJobTemplate', null=True)),
                ('workflow_job_template', models.ForeignKey(related_name='workflow_job_template_nodes', default=None, blank=True, to='main.WorkflowJobTemplate', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='workflowjobnode',
            name='unified_job_template',
            field=models.ForeignKey(related_name='workflowjobnodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJobTemplate', null=True),
        ),
        migrations.AddField(
            model_name='workflowjobnode',
            name='workflow_job',
            field=models.ForeignKey(related_name='workflow_job_nodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.WorkflowJob', null=True),
        ),
        migrations.AddField(
            model_name='workflowjob',
            name='workflow_job_template',
            field=models.ForeignKey(related_name='jobs', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.WorkflowJobTemplate', null=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='workflow_job',
            field=models.ManyToManyField(to='main.WorkflowJob', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='workflow_job_node',
            field=models.ManyToManyField(to='main.WorkflowJobNode', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='workflow_job_template',
            field=models.ManyToManyField(to='main.WorkflowJobTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='workflow_job_template_node',
            field=models.ManyToManyField(to='main.WorkflowJobTemplateNode', blank=True),
        ),
        # RBAC, prompting changes
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
