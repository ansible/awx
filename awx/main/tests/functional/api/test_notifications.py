import pytest

from awx.api.versioning import reverse


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
