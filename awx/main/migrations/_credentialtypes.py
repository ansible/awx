from awx.main import utils
from awx.main.models import CredentialType
from awx.main.utils.encryption import encrypt_field, decrypt_field
from django.db.models import Q


DEPRECATED_CRED_KIND = {
    'rax': {
        'kind': 'cloud',
        'name': 'Rackspace',
        'inputs': {
            'fields': [{
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
            }],
            'required': ['username', 'password']
        },
        'injectors': {
            'env': {
                'RAX_USERNAME': '{{ username }}',
                'RAX_API_KEY': '{{ password }}',
                'CLOUD_VERIFY_SSL': 'False',
            },
        },
    },
}


def _generate_deprecated_cred_types():
    ret = {}
    for deprecated_kind in DEPRECATED_CRED_KIND:
        ret[deprecated_kind] = None
    return ret


def _populate_deprecated_cred_types(cred, kind):
    if kind not in cred:
        return None
    if cred[kind] is None:
        new_obj = CredentialType(**DEPRECATED_CRED_KIND[kind])
        new_obj.save()
        cred[kind] = new_obj
    return cred[kind]


def _get_insights_credential_type():
    return CredentialType.objects.get(kind='insights')


def _is_insights_scm(apps, cred):
    return apps.get_model('main', 'Credential').objects.filter(id=cred.id, projects__scm_type='insights').exists()


def _disassociate_non_insights_projects(apps, cred):
    apps.get_model('main', 'Project').objects.filter(~Q(scm_type='insights') & Q(credential=cred)).update(credential=None)


def migrate_to_v2_credentials(apps, schema_editor):
    CredentialType.setup_tower_managed_defaults()
    deprecated_cred = _generate_deprecated_cred_types()

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
            if _is_insights_scm(apps, cred):
                _disassociate_non_insights_projects(apps, cred)
                credential_type = _get_insights_credential_type()
            else:
                credential_type = _populate_deprecated_cred_types(deprecated_cred, cred.kind) or CredentialType.from_v1_kind(cred.kind, data)

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
            if data.get('is_insights', False):
                cred.kind = 'insights'
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

                    # copy rbac roles
                    for role_type in ('read_role', 'admin_role', 'use_role'):
                        for member in getattr(cred, role_type).members.all():
                            getattr(new_cred, role_type).members.add(member)
                        for role in getattr(cred, role_type).parents.all():
                            getattr(new_cred, role_type).parents.add(role)

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


def add_vault_id_field(apps, schema_editor):
    vault_credtype = CredentialType.objects.get(kind='vault')
    vault_credtype.inputs = CredentialType.defaults.get('vault')().inputs
    vault_credtype.save()


def remove_vault_id_field(apps, schema_editor):
    vault_credtype = CredentialType.objects.get(kind='vault')
    idx = 0
    for i, input in enumerate(vault_credtype.inputs['fields']):
        if input['id'] == 'vault_id':
            idx = i
            break
    vault_credtype.inputs['fields'].pop(idx)
    vault_credtype.save()


def create_rhv_tower_credtype(apps, schema_editor):
    CredentialType.setup_tower_managed_defaults()


def add_tower_verify_field(apps, schema_editor):
    tower_credtype = CredentialType.objects.get(
        kind='cloud', name='Ansible Tower', managed_by_tower=True
    )
    tower_credtype.inputs = CredentialType.defaults.get('tower')().inputs
    tower_credtype.save()


def add_azure_cloud_environment_field(apps, schema_editor):
    azure_rm_credtype = CredentialType.objects.get(kind='cloud',
                                                   name='Microsoft Azure Resource Manager')
    azure_rm_credtype.inputs = CredentialType.defaults.get('azure_rm')().inputs
    azure_rm_credtype.save()


def remove_become_methods(apps, schema_editor):
    become_credtype = CredentialType.objects.filter(kind='ssh', managed_by_tower=True).first()
    become_credtype.inputs = CredentialType.defaults.get('ssh')().inputs
    become_credtype.save()


def add_openstack_verify_field(apps, schema_editor):
    openstack_credtype = CredentialType.objects.get(
        kind='cloud', name='OpenStack', managed_by_tower=True
    )
    openstack_credtype.inputs = CredentialType.defaults.get('openstack')().inputs
    openstack_credtype.save()
