from django.db import migrations
from awx.main.models import CredentialType


def update_github_app_namespace(apps, schema_editor):
    CredentialType.setup_tower_managed_defaults(apps)
    apps.get_model('main', 'CredentialType').objects.filter(namespace='github_app').update(namespace='github_app_lookup')


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0202_squashed_deletions.py'),
    ]

    operations = [migrations.RunPython(update_github_app_namespace)]
