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


@pytest.mark.django_db
def test_organization_auditor_role(rando, setup_managed_roles, organization, inventory, project, jt_linked):
    obj_list = (inventory, project, jt_linked)
    for obj in obj_list:
        assert obj.organization == organization, obj  # sanity

    assert [rando.has_obj_perm(obj, 'view') for obj in obj_list] == [False for i in range(3)], obj_list

    rd = RoleDefinition.objects.get(name='Organization Audit')
    rd.give_permission(rando, organization)

    codename_set = set(rd.permissions.values_list('codename', flat=True))
    assert not ({'view_inventory', 'view_jobtemplate', 'audit_organization'} - codename_set)  # sanity

    assert [obj in type(obj).access_qs(rando) for obj in obj_list] == [True for i in range(3)], obj_list
    assert [rando.has_obj_perm(obj, 'view') for obj in obj_list] == [True for i in range(3)], obj_list
