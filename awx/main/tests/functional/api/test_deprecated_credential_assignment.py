import mock
import pytest

from awx.main.models import Credential, Job
from awx.api.versioning import reverse


@pytest.fixture
def job_template(job_template, project, inventory):
    job_template.playbook = 'helloworld.yml'
    job_template.project = project
    job_template.inventory = inventory
    job_template.ask_credential_on_launch = True
    job_template.save()
    return job_template


@pytest.mark.django_db
@pytest.mark.parametrize('key', ('credential', 'vault_credential'))
def test_credential_access_empty(get, job_template, admin, key):
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    resp = get(url, admin)
    assert resp.data[key] is None
    assert key not in resp.data['summary_fields']


@pytest.mark.django_db
def test_ssh_credential_access(get, job_template, admin, machine_credential):
    job_template.credentials.add(machine_credential)
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    resp = get(url, admin)
    assert resp.data['credential'] == machine_credential.pk
    assert resp.data['summary_fields']['credential']['credential_type_id'] == machine_credential.pk
    assert resp.data['summary_fields']['credential']['kind'] == 'ssh'


@pytest.mark.django_db
def test_ssh_credential_update(get, patch, job_template, admin, machine_credential):
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    patch(url, {'credential': machine_credential.pk}, admin, expect=200)
    resp = get(url, admin)
    assert resp.data['credential'] == machine_credential.pk


@pytest.mark.django_db
def test_ssh_credential_update_invalid_kind(get, patch, job_template, admin, vault_credential):
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    resp = patch(url, {'credential': vault_credential.pk}, admin, expect=400)
    assert 'You must provide an SSH credential.' in resp.content


@pytest.mark.django_db
def test_vault_credential_access(get, job_template, admin, vault_credential):
    job_template.credentials.add(vault_credential)
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    resp = get(url, admin)
    assert resp.data['vault_credential'] == vault_credential.pk
    assert resp.data['summary_fields']['vault_credential']['credential_type_id'] == vault_credential.pk  # noqa
    assert resp.data['summary_fields']['vault_credential']['kind'] == 'vault'


@pytest.mark.django_db
def test_vault_credential_update(get, patch, job_template, admin, vault_credential):
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    patch(url, {'vault_credential': vault_credential.pk}, admin, expect=200)
    resp = get(url, admin)
    assert resp.data['vault_credential'] == vault_credential.pk


@pytest.mark.django_db
def test_vault_credential_update_invalid_kind(get, patch, job_template, admin,
                                              machine_credential):
    url = reverse('api:job_template_detail', kwargs={'pk': job_template.pk})
    resp = patch(url, {'vault_credential': machine_credential.pk}, admin, expect=400)
    assert 'You must provide a vault credential.' in resp.content


@pytest.mark.django_db
def test_extra_credentials_filtering(get, job_template, admin,
                                     machine_credential, vault_credential, credential):
    job_template.credentials.add(machine_credential)
    job_template.credentials.add(vault_credential)
    job_template.credentials.add(credential)
    url = reverse(
        'api:job_template_extra_credentials_list',
        kwargs={'version': 'v2', 'pk': job_template.pk}
    )
    resp = get(url, admin, expect=200)
    assert resp.data['count'] == 1
    assert resp.data['results'][0]['id'] == credential.pk


@pytest.mark.django_db
def test_extra_credentials_requires_cloud_or_net(get, post, job_template, admin,
                                                 machine_credential, vault_credential, credential,
                                                 net_credential):
    url = reverse(
        'api:job_template_extra_credentials_list',
        kwargs={'version': 'v2', 'pk': job_template.pk}
    )

    for cred in (machine_credential, vault_credential):
        resp = post(url, {'associate': True, 'id': cred.pk}, admin, expect=400)
        assert 'Extra credentials must be network or cloud.' in resp.content

    post(url, {'associate': True, 'id': credential.pk}, admin, expect=204)
    assert get(url, admin).data['count'] == 1

    post(url, {'associate': True, 'id': net_credential.pk}, admin, expect=204)
    assert get(url, admin).data['count'] == 2


@pytest.mark.django_db
def test_prevent_multiple_machine_creds(get, post, job_template, admin, machine_credential):
    url = reverse(
        'api:job_template_credentials_list',
        kwargs={'version': 'v2', 'pk': job_template.pk}
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
    assert 'Cannot assign multiple Machine credentials.' in resp.content


@pytest.mark.django_db
def test_prevent_multiple_machine_creds_at_launch(get, post, job_template, admin, machine_credential):
    other_cred = Credential(credential_type=machine_credential.credential_type, name="Second",
                            inputs={'username': 'bob'})
    other_cred.save()
    creds = [machine_credential.pk, other_cred.pk]
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = post(url, {'credentials': creds}, admin)
    assert 'Cannot assign multiple Machine credentials.' in resp.content


@pytest.mark.django_db
def test_extra_credentials_unique_by_kind(get, post, job_template, admin,
                                          credentialtype_aws):
    url = reverse(
        'api:job_template_extra_credentials_list',
        kwargs={'version': 'v2', 'pk': job_template.pk}
    )

    def _new_cred(name):
        return {
            'name': name,
            'credential_type': credentialtype_aws.pk,
            'inputs': {
                'username': 'bob',
                'password': 'secret',
            }
        }

    post(url, _new_cred('First Cred'), admin, expect=201)
    assert get(url, admin).data['count'] == 1

    resp = post(url, _new_cred('Second Cred'), admin, expect=400)
    assert 'Cannot assign multiple Amazon Web Services credentials.' in resp.content


@pytest.mark.django_db
def test_ssh_credential_at_launch(get, post, job_template, admin, machine_credential):
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'credential': machine_credential.pk}, admin, expect=201).data['job']
    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']

    assert len(summary_fields['credentials']) == 1


@pytest.mark.django_db
def test_vault_credential_at_launch(get, post, job_template, admin, vault_credential):
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'vault_credential': vault_credential.pk}, admin, expect=201).data['job']
    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']

    assert len(summary_fields['credentials']) == 1


@pytest.mark.django_db
def test_extra_credentials_at_launch(get, post, job_template, admin, credential):
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'extra_credentials': [credential.pk]}, admin, expect=201).data['job']
    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']

    assert len(summary_fields['credentials']) == 1


@pytest.mark.django_db
def test_modify_ssh_credential_at_launch(get, post, job_template, admin,
                                         machine_credential, vault_credential, credential):
    job_template.credentials.add(vault_credential)
    job_template.credentials.add(credential)
    job_template.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'credential': machine_credential.pk}, admin, expect=201).data['job']

    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']
    assert len(summary_fields['credentials']) == 3


@pytest.mark.django_db
def test_modify_vault_credential_at_launch(get, post, job_template, admin,
                                           machine_credential, vault_credential, credential):
    job_template.credentials.add(machine_credential)
    job_template.credentials.add(credential)
    job_template.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'vault_credential': vault_credential.pk}, admin, expect=201).data['job']

    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']
    assert len(summary_fields['credentials']) == 3


@pytest.mark.django_db
def test_modify_extra_credentials_at_launch(get, post, job_template, admin,
                                            machine_credential, vault_credential, credential):
    job_template.credentials.add(machine_credential)
    job_template.credentials.add(vault_credential)
    job_template.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'extra_credentials': [credential.pk]}, admin, expect=201).data['job']

    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']
    assert len(summary_fields['credentials']) == 3


@pytest.mark.django_db
def test_overwrite_ssh_credential_at_launch(get, post, job_template, admin, machine_credential):
    job_template.credentials.add(machine_credential)
    job_template.save()

    new_cred = machine_credential
    new_cred.pk = None
    new_cred.save()

    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    pk = post(url, {'credential': new_cred.pk}, admin, expect=201).data['job']

    summary_fields = get(reverse('api:job_detail', kwargs={'pk': pk}), admin).data['summary_fields']
    assert len(summary_fields['credentials']) == 1
    assert summary_fields['credentials'][0]['id'] == new_cred.pk


@pytest.mark.django_db
def test_ssh_password_prompted_at_launch(get, post, job_template, admin, machine_credential):
    job_template.credentials.add(machine_credential)
    job_template.save()
    machine_credential.inputs['password'] = 'ASK'
    machine_credential.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = get(url, admin)
    assert 'ssh_password' in resp.data['passwords_needed_to_start']


@pytest.mark.django_db
def test_prompted_credential_removed_on_launch(get, post, job_template, admin, machine_credential):
    # If a JT has a credential that needs a password, but the launch POST
    # specifies {"credentials": []}, don't require any passwords
    job_template.credentials.add(machine_credential)
    job_template.save()
    machine_credential.inputs['password'] = 'ASK'
    machine_credential.save()
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = post(url, {}, admin, expect=400)
    resp = post(url, {'credentials': []}, admin, expect=201)
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
    job_template.save()
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
def test_extra_creds_prompted_at_launch(get, post, job_template, admin, net_credential):
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    resp = post(url, {'extra_credentials': [net_credential.pk]}, admin, expect=201)

    summary_fields = get(
        reverse('api:job_detail', kwargs={'pk': resp.data['job']}),
        admin
    ).data['summary_fields']
    assert len(summary_fields['credentials']) == 1


@pytest.mark.django_db
def test_invalid_mixed_credentials_specification(get, post, job_template, admin, net_credential):
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    post(url, {'credentials': [net_credential.pk], 'extra_credentials': [net_credential.pk]}, admin, expect=400)


@pytest.mark.django_db
def test_rbac_default_credential_usage(get, post, job_template, alice, machine_credential):
    job_template.credentials.add(machine_credential)
    job_template.execute_role.members.add(alice)
    job_template.save()

    # alice can launch; she's not adding any _new_ credentials, and she has
    # execute access to the JT
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    post(url, {'credential': machine_credential.pk}, alice, expect=201)

    # make (copy) a _new_ SSH cred
    new_cred = Credential.objects.create(
        name=machine_credential.name,
        credential_type=machine_credential.credential_type,
        inputs=machine_credential.inputs
    )

    # alice is attempting to launch with a *different* SSH cred, but
    # she does not have access to it, so she cannot launch
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    post(url, {'credential': new_cred.pk}, alice, expect=403)

    # if alice has gains access to the credential, she *can* launch
    new_cred.use_role.members.add(alice)
    url = reverse('api:job_template_launch', kwargs={'pk': job_template.pk})
    post(url, {'credential': new_cred.pk}, alice, expect=201)
