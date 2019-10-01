from django.db import (
    migrations,
    models,
)
import jsonfield.fields
import awx.main.fields

from awx.main.migrations import _save_password_keys
from awx.main.migrations import _migration_utils as migration_utils


def update_dashed_host_variables(apps, schema_editor):
    Host = apps.get_model('main', 'Host')
    for host in Host.objects.filter(variables='---'):
        host.variables = ''
        host.save()


SQUASHED_30 = {
    '0029_v302_add_ask_skip_tags': [
        # add ask skip tags
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_skip_tags_on_launch',
            field=models.BooleanField(default=False),
        ),
    ],
    '0030_v302_job_survey_passwords': [
        # job survery passwords
        migrations.AddField(
            model_name='job',
            name='survey_passwords',
            field=jsonfield.fields.JSONField(default=dict, editable=False, blank=True),
        ),
    ],
    '0031_v302_migrate_survey_passwords': [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(_save_password_keys.migrate_survey_passwords),
    ],
    '0032_v302_credential_permissions_update': [
        # RBAC credential permission updates
        migrations.AlterField(
            model_name='credential',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['singleton:system_administrator', 'organization.admin_role'], to='main.Role', null='True'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['admin_role'], to='main.Role', null='True'),
        ),
    ],
    '0033_v303_v245_host_variable_fix': [
        migrations.RunPython(migration_utils.set_current_apps_for_migrations),
        migrations.RunPython(update_dashed_host_variables),
    ],
}


__all__ = ['SQUASHED_30']
