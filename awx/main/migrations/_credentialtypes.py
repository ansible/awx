from awx.main import utils
from awx.main.models import CredentialType
from awx.main.utils.common import encrypt_field, decrypt_field


def migrate_to_v2_credentials(apps, schema_editor):
    CredentialType.setup_tower_managed_defaults()

    # this monkey-patch is necessary to make the implicit role generation save
    # signal use the correct Role model (the version active at this point in
    # migration, not the one at HEAD)
    orig_current_apps = utils.get_current_apps
    try:
        utils.get_current_apps = lambda: apps
        for cred in apps.get_model('main', 'Credential').objects.all():
            job_templates = cred.jobtemplates.all()
            jobs = cred.jobs.all()
            data = {}
            if getattr(cred, 'vault_password', None):
                data['vault_password'] = cred.vault_password
            credential_type = CredentialType.from_v1_kind(cred.kind, data)
            defined_fields = credential_type.defined_fields
            cred.credential_type = apps.get_model('main', 'CredentialType').objects.get(pk=credential_type.pk)

            for field in defined_fields:
                if getattr(cred, field, None):
                    cred.inputs[field] = getattr(cred, field)
            if cred.vault_password:
                for jt in job_templates:
                    jt.credential = None
                    jt.vault_credential = cred
                    jt.save()
                for job in jobs:
                    job.credential = None
                    job.vault_credential = cred
                    job.save()
            cred.save()

            #
            # If the credential contains a vault password, create a new
            # *additional* credential for the ssh details
            #
            if cred.vault_password:
                # We need to make an ssh credential, too
                ssh_type = CredentialType.from_v1_kind('ssh')
                new_cred = apps.get_model('main', 'Credential').objects.get(pk=cred.pk)
                new_cred.pk = None
                new_cred.vault_password = ''
                new_cred.credential_type = apps.get_model('main', 'CredentialType').objects.get(pk=ssh_type.pk)
                if 'vault_password' in new_cred.inputs:
                    del new_cred.inputs['vault_password']

                # unset these attributes so that new roles are properly created
                # at save time
                new_cred.read_role = None
                new_cred.admin_role = None
                new_cred.use_role = None

                if any([getattr(cred, field) for field in ssh_type.defined_fields]):
                    new_cred.save(force_insert=True)

                    for jt in job_templates:
                        jt.credential = new_cred
                        jt.save()
                    for job in jobs:
                        job.credential = new_cred
                        job.save()

                    # passwords must be decrypted and re-encrypted, because
                    # their encryption is based on the Credential's primary key
                    # (which has changed)
                    for field in ssh_type.defined_fields:
                        if field in ssh_type.secret_fields:
                            value = decrypt_field(cred, field)
                            if value:
                                setattr(new_cred, field, value)
                                new_cred.inputs[field] = encrypt_field(new_cred, field)
                                setattr(new_cred, field, '')
                        elif getattr(cred, field):
                            new_cred.inputs[field] = getattr(cred, field)
                    new_cred.save()
    finally:
        utils.get_current_apps = orig_current_apps


def migrate_job_credentials(apps, schema_editor):
    # this monkey-patch is necessary to make the implicit role generation save
    # signal use the correct Role model (the version active at this point in
    # migration, not the one at HEAD)
    orig_current_apps = utils.get_current_apps
    try:
        utils.get_current_apps = lambda: apps
        for type_ in ('Job', 'JobTemplate'):
            for obj in apps.get_model('main', type_).objects.all():
                if obj.cloud_credential:
                    obj.extra_credentials.add(obj.cloud_credential)
                if obj.network_credential:
                    obj.extra_credentials.add(obj.network_credential)
                obj.save()
    finally:
        utils.get_current_apps = orig_current_apps
