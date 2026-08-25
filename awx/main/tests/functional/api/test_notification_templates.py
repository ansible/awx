# -*- coding: utf-8 -*-
import pytest

from awx.api.versioning import reverse
from awx.main.models import NotificationTemplate, Organization


@pytest.mark.django_db
def test_notification_template_names_unique_per_organization(post, admin_user):
    """
    Validate that notification templates must have unique names within an organization,
    but can have the same name across different organizations.
    """
    org1 = Organization.objects.create(name='org-notif-1')
    org2 = Organization.objects.create(name='org-notif-2')
    template_name = 'SharedNotificationName'

    # Create notification template in org1
    resp1 = post(
        reverse('api:notification_template_list'),
        {
            'name': template_name,
            'organization': org1.id,
            'notification_type': 'email',
            'notification_configuration': {
                'username': 'user@example.com',
                'password': 'pass',
                'sender': 'sender@example.com',
                'recipients': ['recipient@example.com'],
                'host': 'smtp.example.com',
                'port': 25,
                'use_tls': False,
                'use_ssl': False,
            },
        },
        admin_user,
        expect=201,
    )
    template1_id = resp1.data['id']

    # Create notification template with same name in org2 - should succeed
    resp2 = post(
        reverse('api:notification_template_list'),
        {
            'name': template_name,
            'organization': org2.id,
            'notification_type': 'email',
            'notification_configuration': {
                'username': 'user@example.com',
                'password': 'pass',
                'sender': 'sender@example.com',
                'recipients': ['recipient@example.com'],
                'host': 'smtp.example.com',
                'port': 25,
                'use_tls': False,
                'use_ssl': False,
            },
        },
        admin_user,
        expect=201,
    )
    template2_id = resp2.data['id']

    assert template1_id != template2_id
    template1 = NotificationTemplate.objects.get(id=template1_id)
    template2 = NotificationTemplate.objects.get(id=template2_id)
    assert template1.name == template2.name == template_name
    assert template1.organization.id == org1.id
    assert template2.organization.id == org2.id

    # Attempt to create another notification template with same name in org1 - should fail
    resp3 = post(
        reverse('api:notification_template_list'),
        {
            'name': template_name,
            'organization': org1.id,
            'notification_type': 'email',
            'notification_configuration': {
                'username': 'user@example.com',
                'password': 'pass',
                'sender': 'sender@example.com',
                'recipients': ['recipient@example.com'],
                'host': 'smtp.example.com',
                'port': 25,
                'use_tls': False,
                'use_ssl': False,
            },
        },
        admin_user,
        expect=400,
    )
    assert 'Notification template with this Organization and Name already exists' in str(resp3.data)
