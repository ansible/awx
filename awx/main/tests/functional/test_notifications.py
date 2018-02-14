import mock
import pytest

from requests.adapters import HTTPAdapter
from requests.utils import select_proxy
from requests.exceptions import ConnectionError

from six.moves import xrange

from awx.api.versioning import reverse
from awx.main.models.notifications import NotificationTemplate, Notification
from awx.main.models.inventory import Inventory, InventorySource
from awx.main.models.jobs import JobTemplate


@pytest.mark.django_db
def test_get_notification_template_list(get, user, notification_template):
    url = reverse('api:notification_template_list')
    response = get(url, user('admin', True))
    assert response.status_code == 200
    assert len(response.data['results']) == 1


@pytest.mark.django_db
def test_basic_parameterization(get, post, user, organization):
    u = user('admin-poster', True)
    url = reverse('api:notification_template_list')
    response = post(url,
                    dict(name="test-webhook",
                         description="test webhook",
                         organization=organization.id,
                         notification_type="webhook",
                         notification_configuration=dict(url="http://localhost",
                                                         headers={"Test": "Header"})),
                    u)
    assert response.status_code == 201
    url = reverse('api:notification_template_detail', kwargs={'pk': response.data['id']})
    response = get(url, u)
    assert 'related' in response.data
    assert 'organization' in response.data['related']
    assert 'summary_fields' in response.data
    assert 'organization' in response.data['summary_fields']
    assert 'notifications' in response.data['related']
    assert 'notification_configuration' in response.data
    assert 'url' in response.data['notification_configuration']
    assert 'headers' in response.data['notification_configuration']


@pytest.mark.django_db
def test_encrypted_subfields(get, post, user, organization):
    def assert_send(self, messages):
        assert self.account_token == "shouldhide"
        return 1
    u = user('admin-poster', True)
    url = reverse('api:notification_template_list')
    response = post(url,
                    dict(name="test-twilio",
                         description="test twilio",
                         organization=organization.id,
                         notification_type="twilio",
                         notification_configuration=dict(account_sid="dummy",
                                                         account_token="shouldhide",
                                                         from_number="+19999999999",
                                                         to_numbers=["9998887777"])),
                    u)
    assert response.status_code == 201
    notification_template_actual = NotificationTemplate.objects.get(id=response.data['id'])
    url = reverse('api:notification_template_detail', kwargs={'pk': response.data['id']})
    response = get(url, u)
    assert response.data['notification_configuration']['account_token'] == "$encrypted$"
    with mock.patch.object(notification_template_actual.notification_class, "send_messages", assert_send):
        notification_template_actual.send("Test", {'body': "Test"})


@pytest.mark.django_db
def test_inherited_notification_templates(get, post, user, organization, project):
    u = user('admin-poster', True)
    url = reverse('api:notification_template_list')
    notification_templates = []
    for nfiers in xrange(3):
        response = post(url,
                        dict(name="test-webhook-{}".format(nfiers),
                             description="test webhook {}".format(nfiers),
                             organization=organization.id,
                             notification_type="webhook",
                             notification_configuration=dict(url="http://localhost",
                                                             headers={"Test": "Header"})),
                        u)
        assert response.status_code == 201
        notification_templates.append(response.data['id'])
    i = Inventory.objects.create(name='test', organization=organization)
    i.save()
    isrc = InventorySource.objects.create(name='test', inventory=i)
    isrc.save()
    jt = JobTemplate.objects.create(name='test', inventory=i, project=project, playbook='debug.yml')
    jt.save()
    url = reverse('api:organization_notification_templates_any_list', kwargs={'pk': organization.id})
    response = post(url, dict(id=notification_templates[0]), u)
    assert response.status_code == 204
    url = reverse('api:project_notification_templates_any_list', kwargs={'pk': project.id})
    response = post(url, dict(id=notification_templates[1]), u)
    assert response.status_code == 204
    url = reverse('api:job_template_notification_templates_any_list', kwargs={'pk': jt.id})
    response = post(url, dict(id=notification_templates[2]), u)
    assert response.status_code == 204
    assert len(jt.notification_templates['any']) == 3
    assert len(project.notification_templates['any']) == 2
    assert len(isrc.notification_templates['any']) == 1


@pytest.mark.django_db
def test_notification_template_merging(get, post, user, organization, project, notification_template):
    user('admin-poster', True)
    organization.notification_templates_any.add(notification_template)
    project.notification_templates_any.add(notification_template)
    assert len(project.notification_templates['any']) == 1


@pytest.mark.django_db
def test_notification_template_simple_patch(patch, notification_template, admin):
    patch(reverse('api:notification_template_detail', kwargs={'pk': notification_template.id}), { 'name': 'foo'}, admin, expect=200)


@pytest.mark.django_db
def test_notification_template_invalid_notification_type(patch, notification_template, admin):
    patch(reverse('api:notification_template_detail', kwargs={'pk': notification_template.id}), { 'notification_type': 'invalid'}, admin, expect=400)


@pytest.mark.django_db
def test_disallow_delete_when_notifications_pending(delete, user, notification_template):
    u = user('superuser', True)
    url = reverse('api:notification_template_detail', kwargs={'pk': notification_template.id})
    Notification.objects.create(notification_template=notification_template,
                                status='pending')
    response = delete(url, user=u)
    assert response.status_code == 405


@pytest.mark.django_db
def test_custom_environment_injection(post, user, organization):
    u = user('admin-poster', True)
    url = reverse('api:notification_template_list')
    response = post(url,
                    dict(name="test-webhook",
                         description="test webhook",
                         organization=organization.id,
                         notification_type="webhook",
                         notification_configuration=dict(url="https://example.org",
                                                         headers={"Test": "Header"})),
                    u)
    assert response.status_code == 201
    template = NotificationTemplate.objects.get(pk=response.data['id'])
    with pytest.raises(ConnectionError), \
            mock.patch('django.conf.settings.AWX_TASK_ENV', {'HTTPS_PROXY': '192.168.50.100:1234'}), \
            mock.patch.object(HTTPAdapter, 'send') as fake_send:
        def _send_side_effect(request, **kw):
            assert select_proxy(request.url, kw['proxies']) == '192.168.50.100:1234'
            raise ConnectionError()
        fake_send.side_effect = _send_side_effect
        template.send('subject', 'message')
