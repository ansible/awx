from awx.main.models import CredentialType
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


def add_vault_id_field(apps, schema_editor):
    # this is no longer necessary; schemas are defined in code
    pass


def remove_vault_id_field(apps, schema_editor):
    # this is no longer necessary; schemas are defined in code
    pass


def add_tower_verify_field(apps, schema_editor):
    # this is no longer necessary; schemas are defined in code
    pass


def remove_become_methods(apps, schema_editor):
    # this is no longer necessary; schemas are defined in code
    pass
