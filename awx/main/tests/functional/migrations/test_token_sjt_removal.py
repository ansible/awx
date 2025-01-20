import pytest
from django.apps import apps
from django.utils.timezone import now

from awx.main.migrations._create_system_jobs import delete_clear_tokens_sjt

SJT_NAME = 'Cleanup Expired OAuth 2 Tokens'


def create_cleartokens_jt(apps, schema_editor):
    # Deleted data migration
    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    schedule_time = now_dt.strftime('%Y%m%dT%H%M%SZ')

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='cleanup_tokens',
        defaults=dict(
            name=SJT_NAME,
            description='Cleanup expired OAuth 2 access and refresh tokens',
            polymorphic_ctype=sjt_ct,
            created=now_dt,
            modified=now_dt,
        ),
    )
    if created:
        sched = Schedule(
            name=SJT_NAME,
            rrule='DTSTART:%s RRULE:FREQ=WEEKLY;INTERVAL=1' % schedule_time,
            description='Removes expired OAuth 2 access and refresh tokens',
            enabled=True,
            created=now_dt,
            modified=now_dt,
            extra_data={},
        )
        sched.unified_job_template = sjt
        sched.save()


@pytest.mark.django_db
def test_clear_token_sjt():
    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    create_cleartokens_jt(apps, None)
    qs = SystemJobTemplate.objects.filter(name=SJT_NAME)
    assert qs.count() == 1
    sjt = qs.first()
    assert Schedule.objects.filter(unified_job_template=sjt).count() == 1
    assert Schedule.objects.filter(unified_job_template__systemjobtemplate__name=SJT_NAME).count() == 1

    # Now run the migration logic to remove
    delete_clear_tokens_sjt(apps, None)
    assert SystemJobTemplate.objects.filter(name=SJT_NAME).count() == 0
    # Making sure that the schedule is cleaned up is the main point of this test
    assert Schedule.objects.filter(unified_job_template__systemjobtemplate__name=SJT_NAME).count() == 0
