import logging

from django.utils.timezone import now

logger = logging.getLogger('awx.main.migrations')

__all__ = ['create_clearsessions_jt', 'delete_clear_tokens_sjt']

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
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1' % schedule_time,
            description='Cleans out expired browser sessions',
            enabled=True,
            created=now_dt,
            modified=now_dt,
            extra_data={},
        )
        sched.unified_job_template = sjt
        sched.save()


def delete_clear_tokens_sjt(apps, schema_editor):
    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    for sjt in SystemJobTemplate.objects.filter(job_type='cleanup_tokens'):
        logger.info(f'Deleting system job template id={sjt.id} due to removal of local OAuth2 tokens')
        sjt.delete()
