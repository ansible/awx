import pytest
from django.contrib.auth.models import User
from django.urls import reverse as django_reverse

from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment


@pytest.mark.django_db
def test_service_index_role_user_assignment_permissions(setup_managed_roles, organization, inventory, rando, user, post):
    "Test permission checking under internal /service-index/ RBAC related views"
    user3 = user('user3', False)
    organization.member_role.members.add(user3)
    organization.member_role.members.add(rando)
    # This is super technical, these are internal actions with internal mechanics
    rando.resource_api_actions = "*"

    inv_admin_rd = RoleDefinition.objects.get(name='Inventory Admin')
    url = django_reverse('serviceuserassignment-assign')
    payload = {
        'role_definition': inv_admin_rd.name,
        'user_ansible_id': str(user3.resource.ansible_id),
        'object_id': str(inventory.id),
        'from_service': 'test-service',
    }

    # As just a member of the organization, rando can not give permissions
    assert rando.can_access(User, 'read', user3)
    post(url, data=payload, user=rando, expect=403)
    assert not RoleUserAssignment.objects.filter(user=user3, role_definition=inv_admin_rd, object_id=inventory.id).exists()

    inv_admin_rd.give_permission(rando, inventory)

    # Now, having admin permission, rando can give permissions
    post(url, data=payload, user=rando, expect=201)
    assert RoleUserAssignment.objects.filter(user=user3, role_definition=inv_admin_rd, object_id=inventory.id).exists()
    assert user3.has_obj_perm(inventory, 'change') is True
