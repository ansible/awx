import pytest

from awx.api.versioning import reverse


# TODO: test this with RBAC and lower-priveleged users
@pytest.mark.django_db
def test_extra_credentials(get, organization_factory, job_template_factory, credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.extra_credentials.add(credential)
    jt.save()
    job = jt.create_unified_job()

    url = reverse('api:job_extra_credentials_list', kwargs={'version': 'v2', 'pk': job.pk})
    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1
