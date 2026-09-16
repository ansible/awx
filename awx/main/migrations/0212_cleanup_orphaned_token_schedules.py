import logging

from django.db import migrations

logger = logging.getLogger('awx.main.migrations')


def cleanup_orphaned_token_schedules(apps, schema_editor):
    """Remove orphaned 'Cleanup Expired OAuth 2 Tokens' schedules left behind
    by migration 0204 when cascade delete did not fire for the associated
    SystemJobTemplate.  Also clears any stale next_schedule references."""
    Schedule = apps.get_model('main', 'Schedule')
    UnifiedJobTemplate = apps.get_model('main', 'UnifiedJobTemplate')

    orphaned = Schedule.objects.filter(
        name='Cleanup Expired OAuth 2 Tokens',
    ).exclude(
        unified_job_template_id__in=UnifiedJobTemplate.objects.values('pk'),
    )

    orphan_ids = list(orphaned.values_list('pk', flat=True))
    if not orphan_ids:
        return

    logger.info(f'Cleaning up {len(orphan_ids)} orphaned token cleanup schedule(s): {orphan_ids}')
    stale_refs = UnifiedJobTemplate.objects.filter(next_schedule_id__in=orphan_ids).update(next_schedule=None)
    if stale_refs:
        logger.info(f'Cleared {stale_refs} stale next_schedule reference(s)')
    orphaned.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0211_create_metrics_utility_functions'),
    ]

    operations = [
        migrations.RunPython(cleanup_orphaned_token_schedules, migrations.RunPython.noop),
    ]
