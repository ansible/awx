# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0043_v310_scm_revision'),
    ]

    operations = [
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
            field=models.TextField(default=b'', editable=False),
        ),
        migrations.AddField(
            model_name='adhoccommandevent',
            name='uuid',
            field=models.CharField(default=b'', max_length=1024, editable=False),
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
            field=models.CharField(default=b'', max_length=1024, editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='start_line',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='jobevent',
            name='stdout',
            field=models.TextField(default=b'', editable=False),
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
            field=models.CharField(max_length=100, choices=[(b'runner_on_failed', 'Host Failed'), (b'runner_on_ok', 'Host OK'), (b'runner_on_unreachable', 'Host Unreachable'), (b'runner_on_skipped', 'Host Skipped'), (b'debug', 'Debug'), (b'verbose', 'Verbose'), (b'deprecated', 'Deprecated'), (b'warning', 'Warning'), (b'system_warning', 'System Warning'), (b'error', 'Error')]),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='counter',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='jobevent',
            name='event',
            field=models.CharField(max_length=100, choices=[(b'runner_on_failed', 'Host Failed'), (b'runner_on_ok', 'Host OK'), (b'runner_on_error', 'Host Failure'), (b'runner_on_skipped', 'Host Skipped'), (b'runner_on_unreachable', 'Host Unreachable'), (b'runner_on_no_hosts', 'No Hosts Remaining'), (b'runner_on_async_poll', 'Host Polling'), (b'runner_on_async_ok', 'Host Async OK'), (b'runner_on_async_failed', 'Host Async Failure'), (b'runner_on_file_diff', 'File Difference'), (b'playbook_on_start', 'Playbook Started'), (b'playbook_on_notify', 'Running Handlers'), (b'playbook_on_no_hosts_matched', 'No Hosts Matched'), (b'playbook_on_no_hosts_remaining', 'No Hosts Remaining'), (b'playbook_on_task_start', 'Task Started'), (b'playbook_on_vars_prompt', 'Variables Prompted'), (b'playbook_on_setup', 'Gathering Facts'), (b'playbook_on_import_for_host', 'internal: on Import for Host'), (b'playbook_on_not_import_for_host', 'internal: on Not Import for Host'), (b'playbook_on_play_start', 'Play Started'), (b'playbook_on_stats', 'Playbook Complete'), (b'debug', 'Debug'), (b'verbose', 'Verbose'), (b'deprecated', 'Deprecated'), (b'warning', 'Warning'), (b'system_warning', 'System Warning'), (b'error', 'Error')]),
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
            index_together=set([('job', 'event'), ('job', 'parent'), ('job', 'start_line'), ('job', 'uuid'), ('job', 'end_line')]),
        ),
    ]
