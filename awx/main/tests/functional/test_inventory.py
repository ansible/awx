import pytest

from django.core.urlresolvers import reverse

@pytest.mark.django_db
def test_inventory_source_notification_on_cloud_only(get, post, group, user, notification_template):
    u = user('admin', True)
    g_cloud = group('cloud')
    g_not = group('not_cloud')
    cloud_is = g_cloud.inventory_source
    not_is = g_not.inventory_source
    cloud_is.source = 'ec2'
    cloud_is.save()
    url = reverse('api:inventory_source_notification_templates_any_list', args=(cloud_is.id,))
    response = post(url, dict(id=notification_template.id), u)
    assert response.status_code == 204
    url = reverse('api:inventory_source_notification_templates_success_list', args=(not_is.id,))
    response = post(url, dict(id=notification_template.id), u)
    assert response.status_code == 400
