from __future__ import unicode_literals

from django.db import migrations, models
from awx.main.migrations._create_system_jobs import create_cleanup_schedules_jt


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0187_hop_nodes'),
    ]

    operations = [
        migrations.RunPython(create_cleanup_schedules_jt, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='systemjob',
            name='job_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('cleanup_jobs', 'Remove jobs older than a certain number of days'),
                    ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'),
                    ('cleanup_sessions', 'Removes expired browser sessions from the database'),
                    ('cleanup_tokens', 'Removes expired OAuth 2 access tokens and refresh tokens'),
                    ('cleanup_schedules', 'Removes schedules without next run'),
                ],
                default='',
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name='systemjobtemplate',
            name='job_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('cleanup_jobs', 'Remove jobs older than a certain number of days'),
                    ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'),
                    ('cleanup_sessions', 'Removes expired browser sessions from the database'),
                    ('cleanup_tokens', 'Removes expired OAuth 2 access tokens and refresh tokens'),
                    ('cleanup_schedules', 'Removes schedules without next run'),
                ],
                default='',
                max_length=32,
            ),
        ),
    ]
