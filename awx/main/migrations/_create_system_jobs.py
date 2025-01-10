import logging

from django.utils.timezone import now

logger = logging.getLogger('awx.main.migrations')

'''
These methods are called by migrations to create various system job templates

Create default system job templates if not present. Create default schedules
only if new system job templates were created (i.e. new database).
'''


SYSTEM_JOB_TEMPLATES = {
    'cleanup_jobs': dict(
        name='Cleanup Job Details',
        description='Remove job history',
        schedule_name='Cleanup Job Schedule',
        rrule_template='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=SU',
        extra_data={'days': '120'},
    ),
    'cleanup_activitystream': dict(
        name='Cleanup Activity Stream',
        description='Remove activity stream history',
        schedule_name='Cleanup Activity Schedule',
        rrule_template='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=TU',
        extra_data={'days': '355'},
    ),
    'cleanup_facts': dict(
        name='Cleanup Fact Details',
        description='Remove system tracking history',
        schedule_name='Cleanup Fact Schedule',
        rrule_template='DTSTART:%s RRULE:FREQ=MONTHLY;INTERVAL=1;BYMONTHDAY=1',
        extra_data={'older_than': '120d', 'granularity': '1w'},
    ),
    'cleanup_sessions': dict(
        name='Cleanup Expired Sessions',
        description='Cleans out expired browser sessions',
        schedule_name='Cleanup Expired Sessions',
        schedule_description='Cleans out expired browser sessions',
        rrule_template='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1',
        extra_data={},
    ),
    'cleanup_tokens': dict(
        name='Cleanup Expired OAuth 2 Tokens',
        description='Cleanup expired OAuth 2 access and refresh tokens',
        schedule_name='Cleanup Expired OAuth 2 Tokens',
        schedule_description='Removes expired OAuth 2 access and refresh tokens',
        rrule_template='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1',
        extra_data={},
    ),
    'run_health_checks': dict(
        name='Run Execution Node Health Checks',
        description='Run health check on all execution nodes',
        schedule_name='Run Execution Node Health Checks',
        rrule_template='DTSTART:%s RRULE:FREQ=DAILY;INTERVAL=1',
        extra_data={},
    ),
}


def create_system_job_templates(apps, schema_editor):
    """
    Create default system job templates if not present. Create default schedules
    only if new system job templates were created (i.e. new database).
    """

    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    now_str = now_dt.strftime('%Y%m%dT%H%M%SZ')
    job_type_choices = set(job_type for job_type, description in SystemJobTemplate._meta.get_field('job_type').choices)

    for job_type, details in SYSTEM_JOB_TEMPLATES.items():
        if job_type not in job_type_choices:
            continue  # when logic runs before field has updated
        sjt, created = SystemJobTemplate.objects.get_or_create(
            job_type=job_type,
            defaults=dict(
                name=details['name'],
                description=details['description'],
                created=now_dt,
                modified=now_dt,
                polymorphic_ctype=sjt_ct,
            ),
        )
        if created:
            logger.info(f'Created system job {job_type}')
            sched = Schedule(
                name=details['schedule_name'],
                rrule=details['rrule_template'] % now_str,
                description=details.get('schedule_description', 'Automatically Generated Schedule'),
                enabled=True,
                extra_data=details['extra_data'],
                created=now_dt,
                modified=now_dt,
            )
            sched.unified_job_template = sjt
            sched.save()
