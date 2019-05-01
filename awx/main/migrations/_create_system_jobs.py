import random
import logging

from django.db import migrations, models
from django.utils.timezone import now, timedelta

logger = logging.getLogger('awx.main.migrations')

__all__ = ['create_collection_jt', 'create_clearsessions_jt', 'create_cleartokens_jt']

'''
These methods are called by migrations to create various system job templates

Create default system job templates if not present. Create default schedules
only if new system job templates were created (i.e. new database).
'''


def create_clearsessions_jt(apps, schema_editor):

    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    schedule_time = now_dt.strftime('%Y%m%dT%H%M%SZ')

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_sessions',
        defaults=dict(
            name='Cleanup Expired Sessions',
            description='Cleans out expired browser sessions',
            polymorphic_ctype=sjt_ct,
            created=now_dt,
            modified=now_dt,
        ),
    )
    if created:
        sched = Schedule(
            name='Cleanup Expired Sessions',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=1' % schedule_time,
            description='Cleans out expired browser sessions',
            enabled=True,            
            created=now_dt,
            modified=now_dt,
            extra_data={},
        )
        sched.unified_job_template = sjt
        sched.save()


def create_cleartokens_jt(apps, schema_editor):

    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    schedule_time = now_dt.strftime('%Y%m%dT%H%M%SZ')

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_tokens',
        defaults=dict(
            name='Cleanup Expired OAuth 2 Tokens',
            description='Cleanup expired OAuth 2 access and refresh tokens',
            polymorphic_ctype=sjt_ct,
            created=now_dt,
            modified=now_dt,
        ),
    )
    if created:
        sched = Schedule(
            name='Cleanup Expired OAuth 2 Tokens',
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=1' % schedule_time,
            description='Removes expired OAuth 2 access and refresh tokens',
            enabled=True,
            created=now_dt,
            modified=now_dt,
            extra_data={},
        )
        sched.unified_job_template = sjt
        sched.save()
