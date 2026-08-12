import logging

from django.db import migrations

logger = logging.getLogger('awx.main.migrations')


def fix_system_auditor_assignments(apps, schema_editor):
    """
    Corrective migration for a bug in 0192 (migrate_to_new_rbac) where a stale
    loop variable caused old system_auditor members to not receive Platform Auditor.
    """
    Role = apps.get_model('main', 'Role')
    RoleDefinition = apps.get_model('dab_rbac', 'RoleDefinition')
    RoleUserAssignment = apps.get_model('dab_rbac', 'RoleUserAssignment')

    platform_auditor = RoleDefinition.objects.filter(name='Platform Auditor').first()
    if not platform_auditor:
        return

    old_system_auditor = Role.objects.filter(singleton_name='system_auditor').first()
    if not old_system_auditor:
        return

    expected_user_ids = set(old_system_auditor.members.values_list('id', flat=True))
    current_user_ids = set(RoleUserAssignment.objects.filter(role_definition=platform_auditor).values_list('user_id', flat=True))
    missing_user_ids = expected_user_ids - current_user_ids

    for user_id in missing_user_ids:
        RoleUserAssignment.objects.create(user_id=user_id, role_definition=platform_auditor)

    if missing_user_ids:
        logger.info(f'Fixed {len(missing_user_ids)} missing Platform Auditor assignments for old system_auditor members')


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0207_alter_skip_tags_to_textfield'),
    ]

    operations = [
        migrations.RunPython(fix_system_auditor_assignments, migrations.RunPython.noop),
    ]
