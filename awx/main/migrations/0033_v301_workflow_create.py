# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
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
            bases=('main.unifiedjob', models.Model),
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
            name='WorkflowNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('always_nodes', models.ManyToManyField(related_name='parent_always_nodes', to='main.WorkflowNode', blank=True)),
                ('failure_nodes', models.ManyToManyField(related_name='parent_failure_nodes', to='main.WorkflowNode', blank=True)),
                ('job', models.ForeignKey(related_name='workflow_node', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJob', null=True)),
                ('success_nodes', models.ManyToManyField(related_name='parent_success_nodes', to='main.WorkflowNode', blank=True)),
                ('unified_job_template', models.ForeignKey(related_name='unified_jt_workflow_nodes', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJobTemplate', null=True)),
                ('workflow_job_template', models.ForeignKey(related_name='workflow_nodes', to='main.WorkflowJobTemplate')),
            ],
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
            name='workflow_job_template',
            field=models.ManyToManyField(to='main.WorkflowJobTemplate', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='workflow_node',
            field=models.ManyToManyField(to='main.WorkflowNode', blank=True),
        ),
    ]
