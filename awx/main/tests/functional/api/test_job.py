import pytest

from awx.api.versioning import reverse

from awx.main.models import JobTemplate, User


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


@pytest.mark.django_db
def test_job_relaunch_permission_denied_response(
        post, get, inventory, project, credential, net_credential, machine_credential):
    jt = JobTemplate.objects.create(name='testjt', inventory=inventory, project=project,
                                    credential=machine_credential)
    jt_user = User.objects.create(username='jobtemplateuser')
    jt.execute_role.members.add(jt_user)
    job = jt.create_unified_job()

    # User capability is shown for this
    r = get(job.get_absolute_url(), jt_user, expect=200)
    assert r.data['summary_fields']['user_capabilities']['start']

    # Job has prompted extra_credential, launch denied w/ message
    job.extra_credentials.add(net_credential)
    r = post(reverse('api:job_relaunch', kwargs={'pk':job.pk}), {}, jt_user, expect=403)
    assert 'launched with prompted fields' in r.data['detail']
    assert 'do not have permission' in r.data['detail']
