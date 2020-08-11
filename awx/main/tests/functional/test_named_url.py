# -*- coding: utf-8 -*-
import pytest

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from awx.api.versioning import reverse
from awx.main.middleware import URLModificationMiddleware
from awx.main.models import (  # noqa
    Credential, CustomInventoryScript, Group, Host, Instance, InstanceGroup,
    Inventory, InventorySource, JobTemplate, NotificationTemplate,
    Organization, Project, User, WorkflowJobTemplate,
)
from awx.conf import settings_registry


def setup_module(module):
    # In real-world scenario, named url graph structure is populated by __init__
    # of URLModificationMiddleware. The way Django bootstraps ensures the initialization
    # will happen *once and only once*, while the number of initialization is uncontrollable
    # in unit test environment. So it is wrapped by try-except block to mute any
    # unwanted exceptions.
    try:
        URLModificationMiddleware()
    except ImproperlyConfigured:
        pass


def teardown_module(module):
    # settings_registry will be persistent states unless we explicitly clean them up.
    settings_registry.unregister('NAMED_URL_FORMATS')
    settings_registry.unregister('NAMED_URL_GRAPH_NODES')


@pytest.mark.django_db
def test_user(get, admin_user):
    test_user = User.objects.create(username='test_user', password='test_user', is_superuser=False)
    url = reverse('api:user_detail', kwargs={'pk': test_user.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_user/')


@pytest.mark.django_db
def test_team(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_team = test_org.teams.create(name='test_team')
    url = reverse('api:team_detail', kwargs={'pk': test_team.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_team++test_org/')


@pytest.mark.django_db
def test_organization(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    url = reverse('api:organization_detail', kwargs={'pk': test_org.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_org/')


@pytest.mark.django_db
def test_job_template(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_jt = JobTemplate.objects.create(name='test_jt', organization=test_org)
    url = reverse('api:job_template_detail', kwargs={'pk': test_jt.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_jt++test_org/')


@pytest.mark.django_db
def test_job_template_old_way(get, admin_user, mocker):
    test_org = Organization.objects.create(name='test_org')
    test_jt = JobTemplate.objects.create(name='test_jt ♥', organization=test_org)
    url = reverse('api:job_template_detail', kwargs={'pk': test_jt.pk})

    response = get(url, user=admin_user, expect=200)
    new_url = response.data['related']['named_url']
    old_url = '/'.join([url.rsplit('/', 2)[0], test_jt.name, ''])

    assert URLModificationMiddleware._convert_named_url(new_url) == url
    assert URLModificationMiddleware._convert_named_url(old_url) == url


@pytest.mark.django_db
def test_workflow_job_template(get, admin_user):
    test_wfjt = WorkflowJobTemplate.objects.create(name='test_wfjt')
    url = reverse('api:workflow_job_template_detail', kwargs={'pk': test_wfjt.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_wfjt++/')
    test_org = Organization.objects.create(name='test_org')
    test_wfjt.organization = test_org
    test_wfjt.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_wfjt++test_org/')


@pytest.mark.django_db
def test_label(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_label = test_org.labels.create(name='test_label')
    url = reverse('api:label_detail', kwargs={'pk': test_label.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_label++test_org/')


@pytest.mark.django_db
def test_project(get, admin_user):
    test_proj = Project.objects.create(name='test_proj')
    url = reverse('api:project_detail', kwargs={'pk': test_proj.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_proj++/')
    test_org = Organization.objects.create(name='test_org')
    test_proj.organization = test_org
    test_proj.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_proj++test_org/')


@pytest.mark.django_db
def test_notification_template(get, admin_user):
    test_notification_template = NotificationTemplate.objects.create(
        name='test_note', notification_type='slack',
        notification_configuration=dict(channels=["Foo", "Bar"], token="token")
    )
    url = reverse('api:notification_template_detail', kwargs={'pk': test_notification_template.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_note++/')
    test_org = Organization.objects.create(name='test_org')
    test_notification_template.organization = test_org
    test_notification_template.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_note++test_org/')


@pytest.mark.django_db
def test_instance(get, admin_user):
    test_instance = Instance.objects.create(
        uuid=settings.SYSTEM_UUID, hostname="localhost", capacity=100
    )
    url = reverse('api:instance_detail', kwargs={'pk': test_instance.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/localhost/')


@pytest.mark.django_db
def test_instance_group(get, admin_user):
    test_instance_group = InstanceGroup.objects.create(name='Tower')
    url = reverse('api:instance_group_detail', kwargs={'pk': test_instance_group.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/Tower/')


@pytest.mark.django_db
def test_inventory(get, admin_user):
    test_inv = Inventory.objects.create(name='test_inv')
    url = reverse('api:inventory_detail', kwargs={'pk': test_inv.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_inv++/')
    test_org = Organization.objects.create(name='test_org')
    test_inv.organization = test_org
    test_inv.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_inv++test_org/')


@pytest.mark.django_db
def test_host(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_inv = Inventory.objects.create(name='test_inv', organization=test_org)
    test_host = Host.objects.create(name='test_host', inventory=test_inv)
    url = reverse('api:host_detail', kwargs={'pk': test_host.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_host++test_inv++test_org/')


@pytest.mark.django_db
def test_group(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_inv = Inventory.objects.create(name='test_inv', organization=test_org)
    test_group = Group.objects.create(name='test_group', inventory=test_inv)
    url = reverse('api:group_detail', kwargs={'pk': test_group.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_group++test_inv++test_org/')


@pytest.mark.django_db
def test_inventory_source(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_inv = Inventory.objects.create(name='test_inv', organization=test_org)
    test_source = InventorySource.objects.create(
        name='test_source',
        inventory=test_inv,
        source='ec2'
    )
    url = reverse('api:inventory_source_detail', kwargs={'pk': test_source.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_source++test_inv++test_org/')
    test_source.inventory = None
    test_source.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_source++/')


@pytest.mark.django_db
def test_inventory_script(get, admin_user):
    test_script = CustomInventoryScript.objects.create(name='test_script')
    url = reverse('api:inventory_script_detail', kwargs={'pk': test_script.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_script++/')
    test_org = Organization.objects.create(name='test_org')
    test_script.organization = test_org
    test_script.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_script++test_org/')


@pytest.mark.django_db
def test_credential(get, admin_user, credentialtype_ssh):
    test_cred = Credential.objects.create(name='test_cred', credential_type=credentialtype_ssh)
    url = reverse('api:credential_detail', kwargs={'pk': test_cred.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_cred++Machine+ssh++/')


@pytest.mark.django_db
def test_403_vs_404(get):
    cindy = User.objects.create(
        username='cindy',
        password='test_user',
        is_superuser=False
    )
    bob = User.objects.create(
        username='bob',
        password='test_user',
        is_superuser=False
    )

    # bob cannot see cindy, pk lookup should be a 403
    url = reverse('api:user_detail', kwargs={'pk': cindy.pk})
    get(url, user=bob, expect=403)

    # bob cannot see cindy, username lookup should be a 404
    get('/api/v2/users/cindy/', user=bob, expect=404)

    get(f'/api/v2/users/{cindy.pk}/', expect=401)
    get('/api/v2/users/cindy/', expect=404)
