import pytest

from awx.main.access import InstanceGroupAccess, NotificationTemplateAccess

from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
def test_instance_group_object_role_delete(rando, instance_group, setup_managed_roles):
    """Basic functionality of IG object-level admin role function AAP-25506"""
    rd = RoleDefinition.objects.get(name='InstanceGroup Admin')
    rd.give_permission(rando, instance_group)
    access = InstanceGroupAccess(rando)
    assert access.can_delete(instance_group)


@pytest.mark.django_db
def test_notification_template_object_role_change(rando, notification_template, setup_managed_roles):
    """Basic functionality of NT object-level admin role function AAP-25493"""
    rd = RoleDefinition.objects.get(name='NotificationTemplate Admin')
    rd.give_permission(rando, notification_template)
    access = NotificationTemplateAccess(rando)
    assert access.can_change(notification_template, {'name': 'new name'})
