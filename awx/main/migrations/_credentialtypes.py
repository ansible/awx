from django.db.models.signals import post_save
from awx.main.models import Credential, CredentialType


def migrate_to_v2_credentials(apps, schema_editor):
    CredentialType.setup_tower_managed_defaults()

    for cred in apps.get_model('main', 'Credential').objects.all():
        data = {}
        if getattr(cred, 'vault_password', None):
            data['vault_password'] = cred.vault_password
        credential_type = CredentialType.from_v1_kind(cred.kind, data)
        defined_fields = credential_type.defined_fields
        cred.credential_type = apps.get_model('main', 'CredentialType').objects.get(pk=credential_type.pk)

        # temporarily disable implicit role signals; the class we're working on
        # is the "pre-migration" credential model; our signals don't like that
        # it differs from the "post-migration" credential model
        for field in cred.__class__.__implicit_role_fields:
            post_save.disconnect(field, cred.__class__, dispatch_uid='implicit-role-post-save')

        for field in defined_fields:
            if getattr(cred, field, None):
                cred.inputs[field] = getattr(cred, field)
            cred.save()

        #
        # If the credential contains a vault password, create a new
        # *additional* credential with the proper CredentialType; this needs to
        # perform a deep copy of the Credential that considers:
        #
        if cred.vault_password:
            new_fields = {}
            for field in CredentialType.from_v1_kind('ssh').defined_fields:
                if getattr(cred, field, None):
                    new_fields[field] = getattr(cred, field)

            if new_fields:
                # We need to make an ssh credential, too
                new_cred = Credential(credential_type=CredentialType.from_v1_kind('ssh'))
                for field, value in new_fields.items():
                    new_cred.inputs[field] = value

                # TODO: copy RBAC and Job Template assignments
                new_cred.save()

        # re-enable implicit role signals
        for field in cred.__class__.__implicit_role_fields:
            post_save.connect(field._post_save, cred.__class__, True, dispatch_uid='implicit-role-post-save')
