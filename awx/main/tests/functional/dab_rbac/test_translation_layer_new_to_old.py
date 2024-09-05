from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment, RoleTeamAssignment
from ansible_base.lib.utils.response import get_relative_url
import pytest


@pytest.mark.django_db
class TestNewToOld:
    '''
    Tests that the DAB RBAC system is correctly translated to the old RBAC system
    Namely, tests functionality of the _sync_assignments_to_old_rbac signal handler
    '''

    def test_new_to_old_rbac_addition(self, admin, post, inventory, bob, setup_managed_roles):
        '''
        Assign user to Inventory Admin role definition, should be added to inventory.admin_role.members
        '''
        rd = RoleDefinition.objects.get(name='Inventory Admin')

        url = get_relative_url('roleuserassignment-list')
        post(url, user=admin, data={'role_definition': rd.id, 'user': bob.id, 'object_id': inventory.id}, expect=201)
        assert bob in inventory.admin_role.members.all()

    def test_new_to_old_rbac_removal(self, admin, delete, inventory, bob, setup_managed_roles):
        '''
        Remove user from Inventory Admin role definition, should be deleted from inventory.admin_role.members
        '''
        inventory.admin_role.members.add(bob)

        rd = RoleDefinition.objects.get(name='Inventory Admin')
        user_assignment = RoleUserAssignment.objects.get(user=bob, role_definition=rd, object_id=inventory.id)

        url = get_relative_url('roleuserassignment-detail', kwargs={'pk': user_assignment.id})
        delete(url, user=admin, expect=204)
        assert bob not in inventory.admin_role.members.all()

    def test_new_to_old_rbac_team_member_addition(self, admin, post, team, bob, setup_managed_roles):
        '''
        Assign user to Controller Team Member role definition, should be added to team.member_role.members
        '''
        rd = RoleDefinition.objects.get(name='Controller Team Member')

        url = get_relative_url('roleuserassignment-list')
        post(url, user=admin, data={'role_definition': rd.id, 'user': bob.id, 'object_id': team.id}, expect=201)
        assert bob in team.member_role.members.all()

    def test_new_to_old_rbac_team_member_removal(self, admin, delete, team, bob):
        '''
        Remove user from Controller Team Member role definition, should be deleted from team.member_role.members
        '''
        team.member_role.members.add(bob)

        rd = RoleDefinition.objects.get(name='Controller Team Member')
        user_assignment = RoleUserAssignment.objects.get(user=bob, role_definition=rd, object_id=team.id)

        url = get_relative_url('roleuserassignment-detail', kwargs={'pk': user_assignment.id})
        delete(url, user=admin, expect=204)
        assert bob not in team.member_role.members.all()

    def test_new_to_old_rbac_team_addition(self, admin, post, team, inventory, setup_managed_roles):
        '''
        Assign team to Inventory Admin role definition, should be added to inventory.admin_role.parents
        '''
        rd = RoleDefinition.objects.get(name='Inventory Admin')

        url = get_relative_url('roleteamassignment-list')
        post(url, user=admin, data={'role_definition': rd.id, 'team': team.id, 'object_id': inventory.id}, expect=201)
        assert team.member_role in inventory.admin_role.parents.all()

    def test_new_to_old_rbac_team_removal(self, admin, delete, team, inventory, setup_managed_roles):
        '''
        Remove team from Inventory Admin role definition, should be deleted from inventory.admin_role.parents
        '''
        inventory.admin_role.parents.add(team.member_role)

        rd = RoleDefinition.objects.get(name='Inventory Admin')
        team_assignment = RoleTeamAssignment.objects.get(team=team, role_definition=rd, object_id=inventory.id)

        url = get_relative_url('roleteamassignment-detail', kwargs={'pk': team_assignment.id})
        delete(url, user=admin, expect=204)
        assert team.member_role not in inventory.admin_role.parents.all()
