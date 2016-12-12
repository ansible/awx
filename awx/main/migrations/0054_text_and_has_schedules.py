# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0053_v310_update_timeout_field_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unifiedjobtemplate',
            name='has_schedules',
        ),
        migrations.AlterField(
            model_name='host',
            name='instance_id',
            field=models.CharField(default=b'', help_text='The value used by the remote inventory source to uniquely identify the host', max_length=1024, blank=True),
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
            field=models.CharField(default=b'', choices=[(b'', 'Manual'), (b'git', 'Git'), (b'hg', 'Mercurial'), (b'svn', 'Subversion')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
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
            field=models.CharField(default=b'', help_text='The location where the project is stored.', max_length=1024, verbose_name='SCM URL', blank=True),
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
            field=models.CharField(default=b'', choices=[(b'', 'Manual'), (b'git', 'Git'), (b'hg', 'Mercurial'), (b'svn', 'Subversion')], max_length=8, blank=True, help_text='Specifies the source control system used to store the project.', verbose_name='SCM Type'),
        ),
        migrations.AlterField(
            model_name='projectupdate',
            name='scm_url',
            field=models.CharField(default=b'', help_text='The location where the project is stored.', max_length=1024, verbose_name='SCM URL', blank=True),
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
            field=models.TextField(default=b'', help_text='The Tower node the job executed on.', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='finished',
            field=models.DateTimeField(default=None, help_text='The date and time the job finished execution.', null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='job_explanation',
            field=models.TextField(default=b'', help_text="A status field to indicate the state of the job if it wasn't able to run and capture stdout", editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='unifiedjob',
            name='started',
            field=models.DateTimeField(default=None, help_text='The date and time the job was queued for starting.', null=True, editable=False),
        ),
    ]
