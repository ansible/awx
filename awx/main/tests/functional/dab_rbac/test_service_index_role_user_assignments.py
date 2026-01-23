import pytest
from django.contrib.auth.models import User
from django.urls import reverse as django_reverse

from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment


@pytest.mark.django_db
def test_service_index_role_user_assignment_permissions(setup_managed_roles, organization, inventory, project, rando, user, post):
    user3 = user('user3', False)
    organization.member_role.members.add(user3)
    organization.member_role.members.add(rando)

    rd = RoleDefinition.objects.get(name='Inventory Admin')
    url = django_reverse('serviceuserassignment-assign')
    payload = {
        'role_definition': rd.name,
        'user_ansible_id': str(user3.resource.ansible_id),
        'object_id': str(inventory.id),
        'from_service': 'test-service',
    }

    assert rando.can_access(User, 'read', user3)
    post(url, data=payload, user=rando, expect=403)

    project_admin_rd = RoleDefinition.objects.get(name='Project Admin')
    project_admin_rd.give_permission(rando, project)
    rando.resource_api_actions = ['assign']
    post(url, data=payload, user=rando, expect=201)

    assert RoleUserAssignment.objects.filter(user=user3, role_definition=rd, object_id=inventory.id).exists()
    assert user3.has_obj_perm(inventory, 'change') is True
