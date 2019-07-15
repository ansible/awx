# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.models.notifications
import jsonfield.fields
import django.db.models.deletion
import awx.main.models.workflow
import awx.main.fields

from . import _squashed
from ._squashed_30 import SQUASHED_30


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_squashed_v300_v303_updates'),
    ]

    replaces = _squashed.replaces(SQUASHED_30) + [
        ('main', '0034_v310_release'),
    ]

    operations = _squashed.operations(SQUASHED_30) + [
        # Create ChannelGroup table
        migrations.CreateModel(
            name='ChannelGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.CharField(unique=True, max_length=200)),
                ('channels', models.TextField()),
            ],
        ),
        # Allow simultaneous Job
        migrations.AddField(
            model_name='job',
            name='allow_simultaneous',
            field=models.BooleanField(default=False),
        ),
        # Job Event UUID
        migrations.AddField(
            model_name='jobevent',
            name='uuid',
            field=models.CharField(default='', max_length=1024, editable=False),
        ),
        # Job Parent Event UUID
        migrations.AddField(
            model_name='jobevent',
            name='parent_uuid',
            field=models.CharField(default='', max_length=1024, editable=False),
        ),
        # Modify the HA Instance
        migrations.RemoveField(
            model_name='instance',
            name='primary',
        ),
        migrations.AlterField(
            model_name='instance',
            name='uuid',
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name='credential',
            name='become_method',
            field=models.CharField(default='', help_text='Privilege escalation method.', max_length=32, blank=True, choices=[('', 'None'), ('sudo', 'Sudo'), ('su', 'Su'), ('pbrun', 'Pbrun'), ('pfexec', 'Pfexec'), ('dzdo', 'DZDO'), ('pmrun', 'Pmrun')]),
        ),
        # Add Workflows
        migrations.AlterField(
            model_name='unifiedjob',
            name='launch_type',
            field=models.CharField(default='manual', max_length=20, editable=False, choices=[('manual', 'Manual'), ('relaunch', 'Relaunch'), ('callback', 'Callback'), ('scheduled', 'Scheduled'), ('dependency', 'Dependency'), ('workflow', 'Workflow'), ('sync', 'Sync')]),
        ),
        migrations.CreateModel(
            name='WorkflowJob',
            fields=[
                ('unifiedjob_ptr', models.OneToOneField(parent_link=True, auto_created=True, on_delete=models.CASCADE, primary_key=True, serialize=False, to='main.UnifiedJob')),
                ('extra_vars', models.TextField(default='', blank=True)),
            ],
            options={
                'ordering': ('id',),
            },
            bases=('main.unifiedjob', models.Model, awx.main.models.notifications.JobNotificationMixin),
        ),
        migrations.CreateModel(
            name='WorkflowJobNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('always_nodes', models.ManyToManyField(related_name='workflowjobnodes_always', to='main.WorkflowJobNode', blank=True)),
                ('failure_nodes', models.ManyToManyField(related_name='workflowjobnodes_failure', to='main.WorkflowJobNode', blank=True)),
                ('job', models.OneToOneField(related_name='unified_job_node', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.UnifiedJob', null=True)),
                ('success_nodes', models.ManyToManyField(related_name='workflowjobnodes_success', to='main.WorkflowJobNode', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkflowJobTemplate',
            fields=[
                ('unifiedjobtemplate_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, on_delete=models.CASCADE, serialize=False, to='main.UnifiedJobTemplate')),
                ('extra_vars', models.TextField(default='', blank=True)),
                ('admin_role', awx.main.fields.ImplicitRoleField(related_name='+', parent_role='singleton:system_administrator', to='main.Role', null='True')),
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
                ('workflow_job_template', models.ForeignKey(related_name='workflow_job_template_nodes', on_delete=models.SET_NULL, default=None, blank=True, to='main.WorkflowJobTemplate', null=True)),
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
            field=models.ForeignKey(related_name='workflow_jobs', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.WorkflowJobTemplate', null=True),
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
        # Workflow RBAC prompts
        migrations.AddField(
            model_name='workflowjobnode',
            name='char_prompts',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
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
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='organization',
            field=models.ForeignKey(related_name='workflows', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='main.Organization', null=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['singleton:system_auditor', 'organization.auditor_role', 'execute_role', 'admin_role'], to='main.Role', null='True'),
        ),
        migrations.AddField(
            model_name='workflowjobtemplatenode',
            name='char_prompts',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
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
            field=models.ForeignKey(related_name='workflow_job_nodes', on_delete=django.db.models.deletion.CASCADE, default=None, blank=True, to='main.WorkflowJob', null=True),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplate',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['singleton:system_administrator', 'organization.admin_role'], to='main.Role', null='True'),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplatenode',
            name='unified_job_template',
            field=models.ForeignKey(related_name='workflowjobtemplatenodes', on_delete=django.db.models.deletion.SET_NULL, default=None, to='main.UnifiedJobTemplate', null=True),
        ),
        # Job artifacts
        migrations.AddField(
            model_name='job',
            name='artifacts',
            field=jsonfield.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='workflowjobnode',
            name='ancestor_artifacts',
            field=jsonfield.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        # Job timeout settings
        migrations.AddField(
            model_name='inventorysource',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='inventoryupdate',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='job',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='projectupdate',
            name='timeout',
            field=models.IntegerField(default=0, blank=True),
        ),
        # Execution Node
        migrations.AddField(
            model_name='unifiedjob',
            name='execution_node',
            field=models.TextField(default='', editable=False, blank=True),
        ),
        # SCM Revision
        migrations.AddField(
            model_name='project',
            name='scm_revision',
            field=models.CharField(default='', editable=False, max_length=1024, blank=True, help_text='The last revision fetched by a project update', verbose_name='SCM Revision'),
        ),
        migrations.AddField(
            model_name='projectupdate',
            name='job_type',
            field=models.CharField(default='check', max_length=64, choices=[('run', 'Run'), ('check', 'Check')]),
        ),
        migrations.AddField(
            model_name='job',
            name='scm_revision',
            field=models.CharField(default='', editable=False, max_length=1024, blank=True, help_text='The SCM Revision from the Project used for this job, if available', verbose_name='SCM Revision'),
        ),
        # Project Playbook Files
        migrations.AddField(
            model_name='project',
            name='playbook_files',
            field=jsonfield.fields.JSONField(default=[], help_text='List of playbooks found in the project', verbose_name='Playbook Files', editable=False, blank=True),
        ),
        # Job events to stdout
        migrations.AddField(
            model_name='adhoccommandevent',
            name='end_line',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='adhoccommandevent',
            name='start_line',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='adhoccommandevent',
            name='stdout',
            field=models.TextField(default='', editable=False),
        ),
        migrations.AddField(
            model_name='adhoccommandevent',
            name='uuid',
            field=models.CharField(default='', max_length=1024, editable=False),
        ),
        migrations.AddField(
            model_name='adhoccommandevent',
            name='verbosity',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='end_line',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='playbook',
            field=models.CharField(default='', max_length=1024, editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='start_line',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='stdout',
            field=models.TextField(default='', editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='verbosity',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='adhoccommandevent',
            name='counter',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='adhoccommandevent',
            name='event',
            field=models.CharField(max_length=100, choices=[('runner_on_failed', 'Host Failed'), ('runner_on_ok', 'Host OK'), ('runner_on_unreachable', 'Host Unreachable'), ('runner_on_skipped', 'Host Skipped'), ('debug', 'Debug'), ('verbose', 'Verbose'), ('deprecated', 'Deprecated'), ('warning', 'Warning'), ('system_warning', 'System Warning'), ('error', 'Error')]),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='counter',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='event',
            field=models.CharField(max_length=100, choices=[('runner_on_failed', 'Host Failed'), ('runner_on_ok', 'Host OK'), ('runner_on_error', 'Host Failure'), ('runner_on_skipped', 'Host Skipped'), ('runner_on_unreachable', 'Host Unreachable'), ('runner_on_no_hosts', 'No Hosts Remaining'), ('runner_on_async_poll', 'Host Polling'), ('runner_on_async_ok', 'Host Async OK'), ('runner_on_async_failed', 'Host Async Failure'), ('runner_item_on_ok', 'Item OK'), ('runner_item_on_failed', 'Item Failed'), ('runner_item_on_skipped', 'Item Skipped'), ('runner_retry', 'Host Retry'), ('runner_on_file_diff', 'File Difference'), ('playbook_on_start', 'Playbook Started'), ('playbook_on_notify', 'Running Handlers'), ('playbook_on_include', 'Including File'), ('playbook_on_no_hosts_matched', 'No Hosts Matched'), ('playbook_on_no_hosts_remaining', 'No Hosts Remaining'), ('playbook_on_task_start', 'Task Started'), ('playbook_on_vars_prompt', 'Variables Prompted'), ('playbook_on_setup', 'Gathering Facts'), ('playbook_on_import_for_host', 'internal: on Import for Host'), ('playbook_on_not_import_for_host', 'internal: on Not Import for Host'), ('playbook_on_play_start', 'Play Started'), ('playbook_on_stats', 'Playbook Complete'), ('debug', 'Debug'), ('verbose', 'Verbose'), ('deprecated', 'Deprecated'), ('warning', 'Warning'), ('system_warning', 'System Warning'), ('error', 'Error')]),
        ),
        migrations.AlterUniqueTogether(
            name='adhoccommandevent',
            unique_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='adhoccommandevent',
            index_together=set([('ad_hoc_command', 'event'), ('ad_hoc_command', 'uuid'), ('ad_hoc_command', 'end_line'), ('ad_hoc_command', 'start_line')]),
        ),
        migrations.AlterIndexTogether(
            name='jobevent',
            index_together=set([('job', 'event'), ('job', 'parent_uuid'), ('job', 'start_line'), ('job', 'uuid'), ('job', 'end_line')]),
        ),
        # Tower state
        migrations.CreateModel(
            name='TowerScheduleState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('schedule_last_run', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        # Tower instance capacity
        migrations.AddField(
            model_name='instance',
            name='capacity',
            field=models.PositiveIntegerField(default=100, editable=False),
        ),
        # Workflow surveys
        migrations.AddField(
            model_name='workflowjob',
            name='survey_passwords',
            field=jsonfield.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='survey_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='workflowjobtemplate',
            name='survey_spec',
            field=jsonfield.fields.JSONField(default=dict, blank=True),
        ),
        # JSON field changes
        migrations.AlterField(
            model_name='adhoccommandevent',
            name='event_data',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='artifacts',
            field=awx.main.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='survey_passwords',
            field=awx.main.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='event_data',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='jobtemplate',
            name='survey_spec',
            field=awx.main.fields.JSONField(default=dict, blank=True),
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
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='job_env',
            field=awx.main.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjob',
            name='survey_passwords',
            field=awx.main.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='ancestor_artifacts',
            field=awx.main.fields.JSONField(default=dict, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobnode',
            name='char_prompts',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplate',
            name='survey_spec',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        migrations.AlterField(
            model_name='workflowjobtemplatenode',
            name='char_prompts',
            field=awx.main.fields.JSONField(default=dict, blank=True),
        ),
        # Job Project Update
        migrations.AddField(
            model_name='job',
            name='project_update',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.ProjectUpdate', help_text='The SCM Refresh task used to make sure the playbooks were available for the job run', null=True),
        ),
        # Inventory, non-unique name
        migrations.AlterField(
            model_name='inventory',
            name='name',
            field=models.CharField(max_length=512),
        ),
        # Text and has schedules
        migrations.RemoveField(
            model_name='unifiedjobtemplate',
            name='has_schedules',
        ),
        migrations.AlterField(
            model_name='host',
            name='instance_id',
            field=models.CharField(default='', help_text='The value used by the remote inventory source to uniquely identify the host', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='scm_clean',
            field=models.BooleanField(default=False, help_text='Discard any local changes before syncing the project.'),
        ),
        migrations.AlterField(
            model_name='project',
            name='scm_delete_on_update',
            field=models.BooleanField(default=False, help_text='Delete the project before syncing.'),
        ),
        migrations.AlterField(
            model_name='project',
            name='scm_type',
            field=models.CharField(default='', choices=[('', 'Manual'), ('git', 'Git'), ('hg', 'Mercurial'), ('svn', 'Subversion')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
        migrations.AlterField(
            model_name='project',
            name='scm_update_cache_timeout',
            field=models.PositiveIntegerField(default=0, help_text='The number of seconds after the last project update ran that a newproject update will be launched as a job dependency.', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='scm_update_on_launch',
            field=models.BooleanField(default=False, help_text='Update the project when a job is launched that uses the project.'),
        ),
        migrations.AlterField(
            model_name='project',
            name='scm_url',
            field=models.CharField(default='', help_text='The location where the project is stored.', max_length=1024, verbose_name='SCM URL', blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_clean',
            field=models.BooleanField(default=False, help_text='Discard any local changes before syncing the project.'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_delete_on_update',
            field=models.BooleanField(default=False, help_text='Delete the project before syncing.'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_type',
            field=models.CharField(default='', choices=[('', 'Manual'), ('git', 'Git'), ('hg', 'Mercurial'), ('svn', 'Subversion')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_url',
            field=models.CharField(default='', help_text='The location where the project is stored.', max_length=1024, verbose_name='SCM URL', blank=True),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='timeout',
            field=models.IntegerField(default=0, help_text='The amount of time to run before the task is canceled.', blank=True),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='dtend',
            field=models.DateTimeField(default=None, help_text='The last occurrence of the schedule occurs before this time, aftewards the schedule expires.', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='dtstart',
            field=models.DateTimeField(default=None, help_text='The first occurrence of the schedule occurs on or after this time.', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='enabled',
            field=models.BooleanField(default=True, help_text='Enables processing of this schedule by Tower.'),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='next_run',
            field=models.DateTimeField(default=None, help_text='The next time that the scheduled action will run.', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='rrule',
            field=models.CharField(help_text='A value representing the schedules iCal recurrence rule.', max_length=255),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='elapsed',
            field=models.DecimalField(help_text='Elapsed time in seconds that the job ran.', editable=False, max_digits=12, decimal_places=3),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='execution_node',
            field=models.TextField(default='', help_text='The Tower node the job executed on.', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='finished',
            field=models.DateTimeField(default=None, help_text='The date and time the job finished execution.', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='job_explanation',
            field=models.TextField(default='', help_text="A status field to indicate the state of the job if it wasn't able to run and capture stdout", editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='started',
            field=models.DateTimeField(default=None, help_text='The date and time the job was queued for starting.', null=True, editable=False),
        ),
    ]
