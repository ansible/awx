import mock
import pytest

from awx.main.models.notifications import Notification, Notifier
from awx.main.models.inventory import Inventory, Group
from awx.main.models.organization import Organization
from awx.main.models.projects import Project
from awx.main.models.jobs import JobTemplate

from django.core.urlresolvers import reverse
from django.core.mail.message import EmailMessage

@pytest.fixture
def notifier():
    return Notifier.objects.create(name="test-notification",
                                   notification_type="webhook",
                                   notification_configuration=dict(url="http://localhost",
                                                                   headers={"Test": "Header"}))

@pytest.mark.django_db
def test_get_notifier_list(get, user, notifier):
    url = reverse('api:notifier_list')
    response = get(url, user('admin', True))
    assert response.status_code == 200
    assert len(response.data['results']) == 1

@pytest.mark.django_db
def test_basic_parameterization(get, post, user, organization):
    u = user('admin-poster', True)
    url = reverse('api:notifier_list')
    response = post(url,
                    dict(name="test-webhook",
                         description="test webhook",
                         organization=1,
                         notification_type="webhook",
                         notification_configuration=dict(url="http://localhost",
                                                         headers={"Test": "Header"})),
                    u)
    assert response.status_code == 201
    url = reverse('api:notifier_detail', args=(response.data['id'],))
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
    url = reverse('api:notifier_list')
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
    notifier_actual = Notifier.objects.get(id=response.data['id'])
    url = reverse('api:notifier_detail', args=(response.data['id'],))
    response = get(url, u)
    assert response.data['notification_configuration']['account_token'] == "$encrypted$"
    with mock.patch.object(notifier_actual.notification_class, "send_messages", assert_send):
        notifier_actual.send("Test", {'body': "Test"})
        
@pytest.mark.django_db
def test_inherited_notifiers(get, post, user, organization, project):
    u = user('admin-poster', True)
    url = reverse('api:notifier_list')
    notifiers = []
    for nfiers in xrange(3):
        response = post(url,
                        dict(name="test-webhook-{}".format(nfiers),
                             description="test webhook {}".format(nfiers),
                             organization=1,
                             notification_type="webhook",
                             notification_configuration=dict(url="http://localhost",
                                                             headers={"Test": "Header"})),
                        u)
        assert response.status_code == 201
        notifiers.append(response.data['id'])
    organization.projects.add(project)
    i = Inventory.objects.create(name='test', organization=organization)
    i.save()
    g = Group.objects.create(name='test', inventory=i)
    g.save()
    jt = JobTemplate.objects.create(name='test', inventory=i, project=project, playbook='debug.yml')
    jt.save()
    url = reverse('api:organization_notifiers_any_list', args=(organization.id,))
    response = post(url, dict(id=notifiers[0]), u)
    assert response.status_code == 204
    url = reverse('api:project_notifiers_any_list', args=(project.id,))
    response = post(url, dict(id=notifiers[1]), u)
    assert response.status_code == 204
    url = reverse('api:job_template_notifiers_any_list', args=(jt.id,))
    response = post(url, dict(id=notifiers[2]), u)
    assert response.status_code == 204
    assert len(jt.notifiers['any']) == 3
    assert len(project.notifiers['any']) == 2
    assert len(g.inventory_source.notifiers['any']) == 1

@pytest.mark.django_db
def test_notifier_merging(get, post, user, organization, project, notifier):
    u = user('admin-poster', True)
    organization.projects.add(project)
    organization.notifiers_any.add(notifier)
    project.notifiers_any.add(notifier)
    assert len(project.notifiers['any']) == 1
