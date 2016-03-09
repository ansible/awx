# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.timezone import now

from awx.api.license import feature_enabled


def create_system_job_templates(apps, schema_editor):
    '''
    Create default system job templates if not present. Create default schedules
    only if new system job templates were created (i.e. new database).
    '''

    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    now_str = now_dt.strftime('%Y%m%dT%H%M%SZ')

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_jobs',
        defaults=dict(
            name='Cleanup Job Details',
            description='Remove job history older than X days',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sjt.schedules.create(
            name='Cleanup Job Schedule',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'days': '120'},
            created=now_dt,
            modified=now_dt,
        )

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_deleted',
        defaults=dict(
            name='Cleanup Deleted Data',
            description='Remove deleted object history older than X days',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sjt.schedules.create(
            name='Cleanup Deleted Data Schedule',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'days': '30'},
            created=now_dt,
            modified=now_dt,
        )

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_activitystream',
        defaults=dict(
            name='Cleanup Activity Stream',
            description='Remove activity stream history older than X days',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sjt.schedules.create(
            name='Cleanup Activity Schedule',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=TU' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'days': '355'},
            created=now_dt,
            modified=now_dt,
        )

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_facts',
        defaults=dict(
            name='Cleanup Fact Details',
            description='Remove system tracking history',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created and feature_enabled('system_tracking', bypass_database=True):
        sjt.schedules.create(
            name='Cleanup Fact Schedule',
            rrule='DTSTART:%s RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=1' % now_str,
            description='Automatically Generated Schedule',
            enabled=True,
            extra_data={'older_than': '120d', 'granularity': '1w'},
            created=now_dt,
            modified=now_dt,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_v300_active_flag_removal'),
    ]

    operations = [
        migrations.RunPython(create_system_job_templates, migrations.RunPython.noop),
    ]
