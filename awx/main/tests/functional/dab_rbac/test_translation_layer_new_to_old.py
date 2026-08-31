import json
from unittest import mock

from ansible_base.rbac.models import ObjectRole, RoleDefinition, RoleUserAssignment, RoleTeamAssignment
from ansible_base.lib.utils.response import get_relative_url
import pytest

from awx.main.models import ActivityStream


@pytest.mark.django_db
class TestNewToOld:
    '''
    Tests that the DAB RBAC system is correctly translated to the old RBAC system
    Namely, tests functionality of the _sync_assignment_to_old_role signal handler
    '''

    def test_new_to_old_rbac_addition(self, admin, post, inventory, bob, setup_managed_roles):
        '''
        Assign user to Inventory Admin role definition, should be added to inventory.admin_role.members
        '''
        rd = RoleDefinition.objects.get(name='Inventory Admin')

        url = get_relative_url('roleuserassignment-list')
        post(url, user=admin, data={'role_definition': rd.id, 'user': bob.id, 'object_id': inventory.id}, expect=201)
        assert bob in inventory.admin_role.members.all()
        # the new-side assignment should be recorded exactly once, not double-recorded via the old-side mirror
        entries = ActivityStream.objects.filter(operation='associate', user=bob)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'user': bob.username,
            'object_type': 'inventory',
            'object_id': inventory.id,
            'object_name': str(inventory),
        }
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'user'

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
        entries = ActivityStream.objects.filter(operation='disassociate', user=bob)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'user': bob.username,
            'object_type': 'inventory',
            'object_id': inventory.id,
            'object_name': str(inventory),
        }
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'user'

    def test_new_to_old_rbac_team_member_addition(self, admin, post, team, bob, setup_managed_roles):
        '''
        Assign user to Team Member role definition, should be added to team.member_role.members
        '''
        rd = RoleDefinition.objects.get(name='Team Member')

        url = get_relative_url('roleuserassignment-list')
        post(url, user=admin, data={'role_definition': rd.id, 'user': bob.id, 'object_id': team.id}, expect=201)
        assert bob in team.member_role.members.all()
        entries = ActivityStream.objects.filter(operation='associate', user=bob)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'user': bob.username,
            'object_type': 'team',
            'object_id': team.id,
            'object_name': str(team),
        }
        assert entry.object1 == 'team'
        assert entry.object2 == 'user'

    def test_new_to_old_rbac_team_member_removal(self, admin, delete, team, bob, setup_managed_roles):
        '''
        Remove user from Team Member role definition, should be deleted from team.member_role.members
        '''
        team.member_role.members.add(bob)

        rd = RoleDefinition.objects.get(name='Team Member')
        user_assignment = RoleUserAssignment.objects.get(user=bob, role_definition=rd, object_id=team.id)

        url = get_relative_url('roleuserassignment-detail', kwargs={'pk': user_assignment.id})
        delete(url, user=admin, expect=204)
        assert bob not in team.member_role.members.all()
        entries = ActivityStream.objects.filter(operation='disassociate', user=bob)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'user': bob.username,
            'object_type': 'team',
            'object_id': team.id,
            'object_name': str(team),
        }
        assert entry.object1 == 'team'
        assert entry.object2 == 'user'

    def test_new_to_old_rbac_team_addition(self, admin, post, team, inventory, setup_managed_roles):
        '''
        Assign team to Inventory Admin role definition, should be added to inventory.admin_role.parents
        '''
        rd = RoleDefinition.objects.get(name='Inventory Admin')

        url = get_relative_url('roleteamassignment-list')
        post(url, user=admin, data={'role_definition': rd.id, 'team': team.id, 'object_id': inventory.id}, expect=201)
        assert team.member_role in inventory.admin_role.parents.all()
        entries = ActivityStream.objects.filter(operation='associate', team=team)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'team': str(team),
            'object_type': 'inventory',
            'object_id': inventory.id,
            'object_name': str(inventory),
        }
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'team'

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
        entries = ActivityStream.objects.filter(operation='disassociate', team=team)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'team': str(team),
            'object_type': 'inventory',
            'object_id': inventory.id,
            'object_name': str(inventory),
        }
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'team'

    def test_flush_rbac_cleanup_skips_sync(self, inventory, bob, setup_managed_roles):
        """Simulate what defer_rbac_computations._flush_rbac does on exit:
        it bulk-deletes ObjectRoles for deleted objects.  Those ObjectRole
        deletions cascade to RoleUserAssignment via the object_role FK.

        Django sets origin to the *initiating* QuerySet, so the cascaded
        assignment post_delete receives origin=<QuerySet of ObjectRole>.
        origin.model (ObjectRole) differs from type(instance) (RoleUserAssignment),
        identifying this as a cascade from a parent model.  The sync handler
        must skip this — the parent objects are already gone and old Role
        M2M entries cascade-deleted from the same parent."""
        from django.db.models import QuerySet
        from django.db.models.signals import post_delete

        rd = RoleDefinition.objects.get(name='Inventory Admin')
        rd.give_permission(bob, inventory)
        assert bob in inventory.admin_role.members.all()

        # Capture the origin kwarg to verify its type empirically
        captured_origins = []

        def capture_origin(sender, instance, origin=None, **kwargs):
            if sender is RoleUserAssignment:
                captured_origins.append(origin)

        post_delete.connect(capture_origin)
        try:
            with mock.patch('awx.main.models.rbac._sync_assignment_to_old_role') as mck:
                # This is what cleanup_deleted_team_roles does:
                ObjectRole.objects.filter(
                    role_definition=rd,
                    object_id=inventory.pk,
                ).delete()
        finally:
            post_delete.disconnect(capture_origin)

        # Verify origin is an ObjectRole QuerySet — a different model
        # than the deleted RoleUserAssignment instance.
        assert len(captured_origins) == 1
        origin = captured_origins[0]
        assert isinstance(origin, QuerySet)
        assert origin.model is ObjectRole
        assert origin.model is not RoleUserAssignment

        # The handler should skip sync for cross-model QuerySet origins
        mck.assert_not_called()

    def test_cascade_from_non_rbac_model_skips_sync(self, organization, inventory, bob, setup_managed_roles):
        """When a non-RBAC parent (Organization) is deleted, cascaded assignment
        deletions should skip the old RBAC sync entirely."""
        rd = RoleDefinition.objects.get(name='Inventory Admin')
        rd.give_permission(bob, inventory)
        assert bob in inventory.admin_role.members.all()

        with mock.patch('awx.main.models.rbac._sync_assignment_to_old_role') as mck:
            organization.delete()

        mck.assert_not_called()

    def test_cascade_team_assignment_from_non_rbac_model_skips_sync(self, organization, team, inventory, setup_managed_roles):
        """When Organization is deleted, Team cascade-deletes via real FK,
        which cascade-deletes RoleTeamAssignment.  Django's Collector sets
        origin to the Organization instance (a Model with app_label != 'dab_rbac'),
        so the sync handler must skip."""
        rd = RoleDefinition.objects.get(name='Inventory Admin')
        rd.give_permission(team, inventory)
        assert RoleTeamAssignment.objects.filter(team=team, role_definition=rd, object_id=inventory.pk).exists()

        with mock.patch('awx.main.models.rbac._sync_assignment_to_old_role') as mck:
            organization.delete()

        mck.assert_not_called()
