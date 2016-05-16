import mock
import pytest

from awx.main.middleware import ActivityStreamMiddleware
from awx.main.models.activity_stream import ActivityStream
from awx.main.access import ActivityStreamAccess

from django.core.urlresolvers import reverse
from django.conf import settings

def mock_feature_enabled(feature, bypass_database=None):
    return True

@pytest.fixture
def activity_stream_entry(organization, rando):
    rando.roles.add(organization.admin_role)
    return ActivityStream.objects.filter(organization__pk=organization.pk, operation='associate').first()

@pytest.mark.skipif(not getattr(settings, 'ACTIVITY_STREAM_ENABLED', True), reason="Activity stream not enabled")
@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_get_activity_stream_list(monkeypatch, organization, get, user):
    url = reverse('api:activity_stream_list')
    response = get(url, user('admin', True))

    assert response.status_code == 200

@pytest.mark.skipif(not getattr(settings, 'ACTIVITY_STREAM_ENABLED', True), reason="Activity stream not enabled")
@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_basic_fields(monkeypatch, organization, get, user):
    u = user('admin', True)
    activity_stream = ActivityStream.objects.filter(organization=organization).latest('pk')
    activity_stream.actor = u
    activity_stream.save()

    aspk = activity_stream.pk
    url = reverse('api:activity_stream_detail', args=(aspk,))
    response = get(url, user('admin', True))

    assert response.status_code == 200
    assert 'related' in response.data
    assert 'organization' in response.data['related']
    assert 'summary_fields' in response.data
    assert 'organization' in response.data['summary_fields']
    assert response.data['summary_fields']['organization'][0]['name'] == 'test-org'

@pytest.mark.skipif(not getattr(settings, 'ACTIVITY_STREAM_ENABLED', True), reason="Activity stream not enabled")
@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_middleware_actor_added(monkeypatch, post, get, user):
    u = user('admin-poster', True)

    url = reverse('api:organization_list')
    response = post(url,
                    dict(name='test-org', description='test-desc'),
                    u,
                    middleware=ActivityStreamMiddleware())
    assert response.status_code == 201

    org_id = response.data['id']
    activity_stream = ActivityStream.objects.filter(organization__pk=org_id).first()

    url = reverse('api:activity_stream_detail', args=(activity_stream.pk,))
    response = get(url, u)

    assert response.status_code == 200
    assert response.data['summary_fields']['actor']['username'] == 'admin-poster'

@pytest.mark.skipif(not getattr(settings, 'ACTIVITY_STREAM_ENABLED', True), reason="Activity stream not enabled")
@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_rbac_stream_resource_roles(activity_stream_entry, organization, rando):

    assert activity_stream_entry.user.first() == rando
    assert activity_stream_entry.organization.first() == organization
    assert activity_stream_entry.role.first() == organization.admin_role
    assert activity_stream_entry.object_relationship_type == 'awx.main.models.organization.Organization.admin_role'

@pytest.mark.skipif(not getattr(settings, 'ACTIVITY_STREAM_ENABLED', True), reason="Activity stream not enabled")
@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_rbac_stream_user_roles(activity_stream_entry, organization, rando):

    assert activity_stream_entry.user.first() == rando
    assert activity_stream_entry.organization.first() == organization
    assert activity_stream_entry.role.first() == organization.admin_role
    assert activity_stream_entry.object_relationship_type == 'awx.main.models.organization.Organization.admin_role'

@pytest.mark.django_db
@pytest.mark.activity_stream_access
@pytest.mark.skipif(not getattr(settings, 'ACTIVITY_STREAM_ENABLED', True), reason="Activity stream not enabled")
@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
def test_stream_access_cant_change(activity_stream_entry, organization, rando):
    access = ActivityStreamAccess(rando)
    # These should always return false because the activity stream can not be edited
    assert not access.can_add(activity_stream_entry)
    assert not access.can_change(activity_stream_entry, {'organization': None})
    assert not access.can_delete(activity_stream_entry)
