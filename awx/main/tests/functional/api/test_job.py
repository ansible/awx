import pytest

from awx.api.versioning import reverse


# TODO: test this with RBAC and lower-priveleged users
@pytest.mark.django_db
def test_extra_credential_creation(get, post, organization_factory, job_template_factory, credentialtype_aws):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    job = jt.create_unified_job()

    url = reverse('api:job_extra_credentials_list', kwargs={'version': 'v2', 'pk': job.pk})
    response = post(url, {
        'name': 'My Cred',
        'credential_type': credentialtype_aws.pk,
        'inputs': {
            'username': 'bob',
            'password': 'secret',
        }
    }, objs.superusers.admin)
    assert response.status_code == 201

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1


# TODO: test this with RBAC and lower-priveleged users
@pytest.mark.django_db
def test_attach_extra_credential(get, post, organization_factory, job_template_factory, credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    job = jt.create_unified_job()

    url = reverse('api:job_extra_credentials_list', kwargs={'version': 'v2', 'pk': job.pk})
    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 0

    response = post(url, {
        'associate': True,
        'id': credential.id,
    }, objs.superusers.admin)
    assert response.status_code == 204

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1


# TODO: test this with RBAC and lower-priveleged users
@pytest.mark.django_db
def test_detach_extra_credential(get, post, organization_factory, job_template_factory, credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.extra_credentials.add(credential)
    jt.save()
    job = jt.create_unified_job()

    url = reverse('api:job_extra_credentials_list', kwargs={'version': 'v2', 'pk': job.pk})
    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1

    response = post(url, {
        'disassociate': True,
        'id': credential.id,
    }, objs.superusers.admin)
    assert response.status_code == 204

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 0


@pytest.mark.django_db
def test_attach_extra_credential_wrong_kind_xfail(get, post, organization_factory, job_template_factory, machine_credential):
    """Extra credentials only allow net + cloud credentials"""
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    job = jt.create_unified_job()

    url = reverse('api:job_extra_credentials_list', kwargs={'version': 'v2', 'pk': job.pk})
    response = post(url, {
        'associate': True,
        'id': machine_credential.id,
    }, objs.superusers.admin)
    assert response.status_code == 400
