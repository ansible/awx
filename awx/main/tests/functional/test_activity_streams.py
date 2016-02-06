import mock
import pytest

from awx.api.views import (
    ActivityStreamList,
    ActivityStreamDetail,
    OrganizationList,
)
from awx.main.middleware import ActivityStreamMiddleware
from awx.main.models.activity_stream import ActivityStream
from django.core.urlresolvers import reverse

def mock_feature_enabled():
    return True

@mock.patch('awx.api.license.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_get_activity_stream_list(monkeypatch, organization, get, user):
    url = reverse('api:activity_stream_list')
    response = get(ActivityStreamList, user('admin', True), url)

    assert response.status_code == 200

@mock.patch('awx.api.license.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_basic_fields(monkeypatch, organization, get, user):
    u = user('admin', True)
    activity_stream = ActivityStream.objects.latest('pk')
    activity_stream.actor = u
    activity_stream.save()

    aspk = activity_stream.pk
    url = reverse('api:activity_stream_detail', args=(aspk,))
    response = get(ActivityStreamDetail, user('admin', True), url, pk=aspk)

    assert response.status_code == 200
    assert 'related' in response.data
    assert 'organization' in response.data['related']
    assert 'summary_fields' in response.data
    assert 'organization' in response.data['summary_fields']
    assert response.data['summary_fields']['organization'][0]['name'] == 'test-org'

@mock.patch('awx.api.license.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_middleware_actor_added(monkeypatch, post, get, user):
    u = user('admin-poster', True)

    url = reverse('api:organization_list')
    response = post(OrganizationList, u, url,
                    kwargs=dict(name='test-org', description='test-desc'),
                    middleware=ActivityStreamMiddleware())
    assert response.status_code == 201

    org_id = response.data['id']
    activity_stream = ActivityStream.objects.filter(organization__pk=org_id).first()

    url = reverse('api:activity_stream_detail', args=(activity_stream.pk,))
    response = get(ActivityStreamDetail, u, url, pk=activity_stream.pk)

    assert response.status_code == 200
    assert response.data['summary_fields']['actor']['username'] == 'admin-poster'
