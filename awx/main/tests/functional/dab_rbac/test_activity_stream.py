import json

import pytest

from awx.api.versioning import reverse

from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment
from ansible_base.rbac import permission_registry

from awx.main.models import ActivityStream, Inventory, Organization


@pytest.mark.django_db
class TestCreatorPermissionActivityStream:
    '''
    give_creator_permissions grants the new-side RoleUserAssignment and mirrors it into
    the legacy Role.members m2m. Only the new-side grant should be recorded - the mirrored
    write must not produce a second entry.
    '''

    def test_object_creation_records_single_entry(self, post, rando, organization, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(
            name='inventory-add',
            permissions=['add_inventory', 'view_organization'],
            content_type=permission_registry.content_type_model.objects.get_for_model(Organization),
        )
        rd.give_permission(rando, organization)

        url = reverse('api:inventory_list')
        response = post(url=url, data={'name': 'rando-created-inventory', 'organization': organization.id}, user=rando, expect=201)
        inventory = Inventory.objects.get(pk=response.data['id'])

        assert rando in inventory.admin_role.members.all()
        entries = ActivityStream.objects.filter(operation='associate', user=rando, changes__icontains='Inventory Admin')
        assert entries.count() == 1
        entry = entries.get()
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'user'


@pytest.mark.django_db
class TestRoleAssignmentActivityStream:
    '''
    Tests that assigning/removing a DAB RBAC role records an ActivityStream entry,
    independent of whether the role has a legacy Role equivalent.
    '''

    def test_custom_role_assignment_recorded(self, rando, inventory, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(
            name='inventory-custom-role',
            permissions=['view_inventory', 'change_inventory'],
            content_type=permission_registry.content_type_model.objects.get_for_model(Inventory),
        )
        rd.give_permission(rando, inventory)

        entries = ActivityStream.objects.filter(operation='associate', user=rando, changes__icontains=rd.name)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {
            'role_definition': rd.name,
            'user': rando.username,
            'object_type': 'inventory',
            'object_id': inventory.id,
            'object_name': str(inventory),
        }
        # object1 is the role's content object and object2 the associated actor, matching
        # the convention used for legacy Role.members association entries, so this reads
        # "disassociated inventory X from user Y" rather than the other way around.
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'user'
        assert entry.object_relationship_type == f'{Inventory.__module__}.Inventory.{rd.id}'

    def test_custom_role_removal_recorded(self, rando, inventory, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(
            name='inventory-custom-role',
            permissions=['view_inventory', 'change_inventory'],
            content_type=permission_registry.content_type_model.objects.get_for_model(Inventory),
        )
        rd.give_permission(rando, inventory)
        rd.remove_permission(rando, inventory)

        entries = ActivityStream.objects.filter(operation='disassociate', user=rando, changes__icontains=rd.name)
        assert entries.count() == 1
        entry = entries.get()
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'user'

    def test_custom_role_team_assignment_recorded(self, team, inventory, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(
            name='inventory-custom-role',
            permissions=['view_inventory', 'change_inventory'],
            content_type=permission_registry.content_type_model.objects.get_for_model(Inventory),
        )
        rd.give_permission(team, inventory)

        entries = ActivityStream.objects.filter(operation='associate', team=team, changes__icontains=rd.name)
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

    def test_custom_role_team_removal_recorded(self, team, inventory, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(
            name='inventory-custom-role',
            permissions=['view_inventory', 'change_inventory'],
            content_type=permission_registry.content_type_model.objects.get_for_model(Inventory),
        )
        rd.give_permission(team, inventory)
        rd.remove_permission(team, inventory)

        entries = ActivityStream.objects.filter(operation='disassociate', team=team, changes__icontains=rd.name)
        assert entries.count() == 1
        entry = entries.get()
        assert entry.object1 == 'inventory'
        assert entry.object2 == 'team'

    def test_global_role_assignment_recorded(self, rando, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(name='global-view-role', content_type=None)
        RoleUserAssignment.objects.create(user=rando, role_definition=rd)

        entries = ActivityStream.objects.filter(operation='associate', user=rando, changes__icontains=rd.name)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {'role_definition': rd.name, 'user': rando.username}
        # No content object for a global role assignment, so object1 is left blank.
        assert entry.object1 == ''
        assert entry.object2 == 'user'
        assert entry.object_relationship_type == str(rd.id)

    def test_cascade_delete_does_not_record_contentless_entry(self, rando, setup_managed_roles):
        '''
        Deleting an object cascade-deletes its RoleUserAssignments. By the time the
        post_delete handler runs, the object is already gone, so there is nothing
        useful to record - it should be skipped rather than logged with no context.
        '''
        org = Organization.objects.create(name='cascade-delete-org')
        rd = RoleDefinition.objects.get(name='Organization Admin')
        rd.give_permission(rando, org)
        assert ActivityStream.objects.filter(operation='associate', user=rando, changes__icontains=rd.name).count() == 1

        org.delete()

        assert ActivityStream.objects.filter(operation='disassociate', user=rando, changes__icontains=rd.name).count() == 0

    def test_cascade_delete_of_team_does_not_leave_dangling_link(self, team, inventory, setup_managed_roles):
        '''
        Deleting a team's organization cascades to delete the team, which cascades to
        delete its RoleTeamAssignments. Recording a fresh ActivityStream entry linked to
        the team in response to that cascade would leave a dangling foreign key once the
        team row is actually removed later in the same cascade - it must be skipped.
        '''
        rd = RoleDefinition.objects.get(name='Inventory Admin')
        rd.give_permission(team, inventory)
        assert ActivityStream.objects.filter(operation='associate', team=team, changes__icontains=rd.name).count() == 1

        team.organization.delete()

        assert ActivityStream.objects.filter(operation='disassociate', team=team, changes__icontains=rd.name).count() == 0
