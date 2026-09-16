import importlib

import pytest
from django.apps import apps
from django.utils.timezone import now

from awx.main.migrations._create_system_jobs import delete_clear_tokens_sjt

_migration_0212 = importlib.import_module('awx.main.migrations.0212_cleanup_orphaned_token_schedules')
cleanup_orphaned_token_schedules = _migration_0212.cleanup_orphaned_token_schedules

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

    delete_clear_tokens_sjt(apps, None)
    assert SystemJobTemplate.objects.filter(name=SJT_NAME).count() == 0
    assert Schedule.objects.filter(name=SJT_NAME).count() == 0


@pytest.mark.django_db
def test_clear_token_sjt_clears_next_schedule():
    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    UnifiedJobTemplate = apps.get_model('main', 'UnifiedJobTemplate')
    create_cleartokens_jt(apps, None)

    sjt = SystemJobTemplate.objects.get(name=SJT_NAME)
    sched = Schedule.objects.get(unified_job_template=sjt)
    UnifiedJobTemplate.objects.filter(pk=sjt.pk).update(next_schedule=sched)

    delete_clear_tokens_sjt(apps, None)
    assert SystemJobTemplate.objects.filter(name=SJT_NAME).count() == 0
    assert Schedule.objects.filter(name=SJT_NAME).count() == 0
    ujt_refs = UnifiedJobTemplate.objects.filter(next_schedule_id=sched.pk).count()
    assert ujt_refs == 0, 'Stale next_schedule references should be cleared'


@pytest.mark.django_db
def test_cleanup_orphaned_token_schedules():
    """Simulate an orphaned schedule (UJT row missing) and verify the
    cleanup migration removes it."""
    Schedule = apps.get_model('main', 'Schedule')
    UnifiedJobTemplate = apps.get_model('main', 'UnifiedJobTemplate')
    create_cleartokens_jt(apps, None)

    sched = Schedule.objects.get(name=SJT_NAME)
    sched_id = sched.pk
    ujt_id = sched.unified_job_template_id

    UnifiedJobTemplate.objects.filter(pk=ujt_id).update(next_schedule=sched)
    # Delete the UJT row directly via SQL to simulate the broken cascade
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM main_systemjobtemplate WHERE unifiedjobtemplate_ptr_id = %s', [ujt_id])
        cursor.execute('DELETE FROM main_unifiedjobtemplate WHERE id = %s', [ujt_id])

    assert Schedule.objects.filter(pk=sched_id).exists(), 'Orphaned schedule should still exist'

    cleanup_orphaned_token_schedules(apps, None)
    assert not Schedule.objects.filter(pk=sched_id).exists(), 'Orphaned schedule should be removed'
