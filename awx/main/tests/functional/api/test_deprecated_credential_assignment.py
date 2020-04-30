from unittest import mock
import pytest

from django.utils.encoding import smart_str
from awx.main.models import Credential, CredentialType, Job
from awx.api.versioning import reverse


@pytest.fixture
def ec2_source(inventory, project):
    with mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.update'):
        return inventory.inventory_sources.create(
            name='some_source', update_on_project_update=True, source='ec2',
            source_project=project, scm_last_revision=project.scm_revision)


@pytest.fixture
def job_template(job_template, project, inventory):
    job_template.playbook = 'helloworld.yml'
    job_template.project = project
    job_template.inventory = inventory
    job_template.ask_credential_on_launch = True
    job_template.save()
    return job_template


@pytest.mark.django_db
def test_prevent_multiple_machine_creds(get, post, job_template, admin, machine_credential):
    url = reverse(
        'api:job_template_credentials_list',
        kwargs={'pk': job_template.pk}
    )

    def _new_cred(name):
        return {
            'name': name,
            'credential_type': machine_credential.credential_type.pk,
            'inputs': {
                'username': 'bob',
                'password': 'secret',
            }
        }

    post(url, _new_cred('First Cred'), admin, expect=201)
    assert get(url, admin).data['count'] == 1

    resp = post(url, _new_cred('Second Cred'), admin, expect=400)
    assert 'Cannot assign multiple Machine credentials.' in smart_str(resp.content)


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['scm', 'insights'])
def test_invalid_credential_type_at_launch(get, post, job_template, admin, kind):
    cred_type = CredentialType.defaults[kind]()
    cred_type.save()
    cred = Credential(
        name='Some Cred',
        credential_type=cred_type,
        inputs={
            'username': 'bob',
            'password': 'secret',
        }
    )
    cred.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})

    resp = post(url, {'credentials': [cred.pk]}, admin, expect=400)
    assert 'Cannot assign a Credential of kind `{}`'.format(kind) in resp.data.get('credentials', [])
    assert Job.objects.count() == 0


@pytest.mark.django_db
def test_prevent_multiple_machine_creds_at_launch(get, post, job_template, admin, machine_credential):
    other_cred = Credential(credential_type=machine_credential.credential_type, name="Second",
                            inputs={'username': 'bob'})
    other_cred.save()
    creds = [machine_credential.pk, other_cred.pk]
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = post(url, {'credentials': creds}, admin)
    assert 'Cannot assign multiple Machine credentials.' in smart_str(resp.content)


@pytest.mark.django_db
def test_ssh_password_prompted_at_launch(get, post, job_template, admin, machine_credential):
    job_template.credentials.add(machine_credential)
    machine_credential.inputs['password'] = 'ASK'
    machine_credential.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = get(url, admin)
    assert 'ssh_password' in resp.data['passwords_needed_to_start']


@pytest.mark.django_db
def test_prompted_credential_replaced_on_launch(get, post, job_template, admin, machine_credential):
    # If a JT has a credential that needs a password, but the launch POST
    # specifies credential that does not require any passwords
    cred2 = Credential(name='second-cred', inputs=machine_credential.inputs,
                       credential_type=machine_credential.credential_type)
    cred2.inputs['password'] = 'ASK'
    cred2.save()
    job_template.credentials.add(cred2)
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = post(url, {}, admin, expect=400)
    resp = post(url, {'credentials': [machine_credential.pk]}, admin, expect=201)
    assert 'job' in resp.data


@pytest.mark.django_db
def test_ssh_credential_with_password_at_launch(get, post, job_template, admin, machine_credential):
    machine_credential.inputs['password'] = 'ASK'
    machine_credential.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = post(url, {'credentials': [machine_credential.pk]}, admin, expect=400)
    assert resp.data['passwords_needed_to_start'] == ['ssh_password']

    with mock.patch.object(Job, 'signal_start') as signal_start:
        resp = post(url, {
            'credentials': [machine_credential.pk],
            'ssh_password': 'testing123'
        }, admin, expect=201)
        signal_start.assert_called_with(ssh_password='testing123')


@pytest.mark.django_db
def test_vault_password_prompted_at_launch(get, post, job_template, admin, vault_credential):
    job_template.credentials.add(vault_credential)
    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = get(url, admin)
    assert 'vault_password' in resp.data['passwords_needed_to_start']


@pytest.mark.django_db
def test_vault_credential_with_password_at_launch(get, post, job_template, admin, vault_credential):
    vault_credential.inputs['vault_password'] = 'ASK'
    vault_credential.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})

    resp = post(url, {'credentials': [vault_credential.pk]}, admin, expect=400)
    assert resp.data['passwords_needed_to_start'] == ['vault_password']

    with mock.patch.object(Job, 'signal_start') as signal_start:
        resp = post(url, {
            'credentials': [vault_credential.pk],
            'vault_password': 'testing123'
        }, admin, expect=201)
        signal_start.assert_called_with(vault_password='testing123')


@pytest.mark.django_db
def test_deprecated_credential_activity_stream(patch, admin_user, machine_credential, job_template):
    job_template.credentials.add(machine_credential)
    starting_entries = job_template.activitystream_set.count()
    # no-op patch
    patch(
        job_template.get_absolute_url(),
        admin_user,
        data={'credential': machine_credential.pk},
        expect=200
    )
    # no-op should not produce activity stream entries
    assert starting_entries == job_template.activitystream_set.count()


@pytest.mark.django_db
def test_multi_vault_preserved_on_put(get, put, admin_user, job_template, vault_credential):
    '''
    A PUT request will necessarily specify deprecated fields, but if the deprecated
    field is a singleton while the `credentials` relation has many, that makes
    it very easy to drop those credentials not specified in the PUT data
    '''
    vault2 = Credential.objects.create(
        name='second-vault',
        credential_type=vault_credential.credential_type,
        inputs={'vault_password': 'foo', 'vault_id': 'foo'}
    )
    job_template.credentials.add(vault_credential, vault2)
    assert job_template.credentials.count() == 2  # sanity check
    r = get(job_template.get_absolute_url(), admin_user, expect=200)
    # should be a no-op PUT request
    put(
        job_template.get_absolute_url(),
        admin_user,
        data=r.data,
        expect=200
    )
    assert job_template.credentials.count() == 2
