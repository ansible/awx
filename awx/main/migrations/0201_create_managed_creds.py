from django.db import migrations

# AWX
from awx.main.models import CredentialType
from awx.main.utils.common import set_current_apps


def setup_tower_managed_defaults(apps, schema_editor):
    set_current_apps(apps)
    CredentialType.setup_tower_managed_defaults(apps)


def setup_rbac_role_system_administrator(apps, schema_editor):
    Role = apps.get_model('main', 'Role')
    Role.objects.get_or_create(singleton_name='system_administrator', role_field='system_administrator')


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0200_template_name_constraint'),
    ]

    operations = [
        migrations.RunPython(setup_tower_managed_defaults),
        migrations.RunPython(setup_rbac_role_system_administrator),
    ]
