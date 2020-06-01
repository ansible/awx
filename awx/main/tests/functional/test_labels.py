import pytest

# awx
from awx.main.models import WorkflowJobTemplate
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_workflow_can_add_label(org_admin,organization, post):
    # create workflow
    wfjt = WorkflowJobTemplate.objects.create(name='test-wfjt')
    wfjt.organization = organization
    # create label
    wfjt.admin_role.members.add(org_admin)
    url = reverse('api:workflow_job_template_label_list', kwargs={'pk': wfjt.pk})
    data = {'name': 'dev-label', 'organization': organization.id}
    label = post(url, user=org_admin, data=data, expect=201)
    assert label.data['name'] == 'dev-label'


@pytest.mark.django_db
def test_workflow_can_remove_label(org_admin, organization, post, get):
    # create workflow
    wfjt = WorkflowJobTemplate.objects.create(name='test-wfjt')
    wfjt.organization = organization
    # create label
    wfjt.admin_role.members.add(org_admin)
    label = wfjt.labels.create(name='dev-label', organization=organization)
    # delete label
    url = reverse('api:workflow_job_template_label_list', kwargs={'pk': wfjt.pk})
    data = {
        "id": label.pk,
        "disassociate": True
    }
    post(url, data, org_admin, expect=204)
    results = get(url, org_admin, expect=200)
    assert results.data['count'] == 0
