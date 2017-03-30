from awx.main.models import CredentialType


def create_tower_managed_credential_types(apps, schema_editor):
    CredentialType.setup_tower_managed_defaults()
