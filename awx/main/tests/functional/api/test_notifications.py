import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_get_org_running_notification(get, admin, organization):
    url = reverse('api:organization_notification_templates_started_list', kwargs={'pk': organization.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_org_running_notification(get, post, admin, notification_template, organization):
    url = reverse('api:organization_notification_templates_started_list', kwargs={'pk': organization.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_get_project_running_notification(get, admin, project):
    url = reverse('api:project_notification_templates_started_list', kwargs={'pk': project.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_project_running_notification(get, post, admin, notification_template, project):
    url = reverse('api:project_notification_templates_started_list', kwargs={'pk': project.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_get_inv_src_running_notification(get, admin, inventory_source):
    url = reverse('api:inventory_source_notification_templates_started_list', kwargs={'pk': inventory_source.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_inv_src_running_notification(get, post, admin, notification_template, inventory_source):
    url = reverse('api:inventory_source_notification_templates_started_list', kwargs={'pk': inventory_source.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_get_jt_running_notification(get, admin, job_template):
    url = reverse('api:job_template_notification_templates_started_list', kwargs={'pk': job_template.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_jt_running_notification(get, post, admin, notification_template, job_template):
    url = reverse('api:job_template_notification_templates_started_list', kwargs={'pk': job_template.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_get_sys_jt_running_notification(get, admin, system_job_template):
    url = reverse('api:system_job_template_notification_templates_started_list', kwargs={'pk': system_job_template.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_sys_jt_running_notification(get, post, admin, notification_template, system_job_template):
    url = reverse('api:system_job_template_notification_templates_started_list', kwargs={'pk': system_job_template.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_get_wfjt_running_notification(get, admin, workflow_job_template):
    url = reverse('api:workflow_job_template_notification_templates_started_list', kwargs={'pk': workflow_job_template.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_wfjt_running_notification(get, post, admin, notification_template, workflow_job_template):
    url = reverse('api:workflow_job_template_notification_templates_started_list', kwargs={'pk': workflow_job_template.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_search_on_notification_configuration_is_prevented(get, admin):
    url = reverse('api:notification_template_list')
    response = get(url, {'notification_configuration__regex': 'ABCDEF'}, admin)
    assert response.status_code == 403
    assert response.data == {"detail": "Filtering on notification_configuration is not allowed."}


@pytest.mark.django_db
def test_get_wfjt_approval_notification(get, admin, workflow_job_template):
    url = reverse('api:workflow_job_template_notification_templates_approvals_list', kwargs={'pk': workflow_job_template.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_wfjt_approval_notification(get, post, admin, notification_template, workflow_job_template):
    url = reverse('api:workflow_job_template_notification_templates_approvals_list', kwargs={'pk': workflow_job_template.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_get_org_approval_notification(get, admin, organization):
    url = reverse('api:organization_notification_templates_approvals_list', kwargs={'pk': organization.pk})
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 0


@pytest.mark.django_db
def test_post_org_approval_notification(get, post, admin, notification_template, organization):
    url = reverse('api:organization_notification_templates_approvals_list', kwargs={'pk': organization.pk})
    response = post(url,
                    dict(id=notification_template.id,
                         associate=True),
                    admin)
    assert response.status_code == 204
    response = get(url, admin)
    assert response.status_code == 200
    assert len(response.data['results']) == 1
