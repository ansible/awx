import json

import pytest

from awx.api.versioning import reverse

from ansible_base.rbac.models import RoleDefinition
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
        # Global (singleton) roles have no content object, so they cannot go through the
        # object-scoped bulk pipeline. give_global_permission is the supported entry point;
        # it routes through the pipeline and fires dab_rbac_assignments_created. A raw
        # RoleUserAssignment.objects.create() would NOT record an entry (see triggers.py).
        rd, _ = RoleDefinition.objects.get_or_create(name='global-view-role', content_type=None)
        rd.give_global_permission(rando)

        entries = ActivityStream.objects.filter(operation='associate', user=rando, changes__icontains=rd.name)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {'role_definition': rd.name, 'user': rando.username}
        # No content object for a global role assignment, so object1 is left blank.
        assert entry.object1 == ''
        assert entry.object2 == 'user'
        assert entry.object_relationship_type == str(rd.id)

    def test_global_role_removal_recorded(self, rando, setup_managed_roles):
        rd, _ = RoleDefinition.objects.get_or_create(name='global-view-role', content_type=None)
        rd.give_global_permission(rando)
        rd.remove_global_permission(rando)

        entries = ActivityStream.objects.filter(operation='disassociate', user=rando, changes__icontains=rd.name)
        assert entries.count() == 1
        entry = entries.get()
        assert json.loads(entry.changes) == {'role_definition': rd.name, 'user': rando.username}
        assert entry.object1 == ''
        assert entry.object2 == 'user'
        assert entry.object_relationship_type == str(rd.id)

    def test_content_object_lookup_batches_by_type(self, rando, organization, django_assert_max_num_queries, setup_managed_roles):
        # The whole point of the bulk-signal migration is to stop resolving each assignment's
        # content object with its own query. _prefetch_assignment_content_objects must fetch
        # all objects of a type in one query regardless of how many assignments there are.
        from ansible_base.rbac.models import RoleUserAssignment

        from awx.main.models import Inventory
        from awx.main.signals import _prefetch_assignment_content_objects

        rd = RoleDefinition.objects.get(name='Inventory Admin')
        inventories = [Inventory.objects.create(name=f'batch-inv-{i}', organization=organization) for i in range(5)]
        for inv in inventories:
            rd.give_permission(rando, inv)

        # Re-fetch so content_object is not already cached on the instances.
        assignments = list(RoleUserAssignment.objects.filter(role_definition=rd, user=rando))
        assert len(assignments) == 5

        # No content_objects supplied (the give_assignments-direct / empty-dict case): the
        # helper must batch — one query for the content types, one in_bulk for the objects —
        # not one query per assignment. Assert a small constant that does not grow with the
        # number of assignments.
        with django_assert_max_num_queries(3):
            lookup = _prefetch_assignment_content_objects(assignments, {})

        for a in assignments:
            assert lookup[(a.content_type_id, a.object_id)].pk == int(a.object_id)

    def test_old_rbac_field_names_resolved_in_one_query(self, django_assert_num_queries, setup_managed_roles):
        # The old-RBAC mirror needs each assignment's role-definition name to find the legacy
        # Role field. _field_names_for_old_rbac must resolve the whole batch in a single query
        # rather than dereferencing instance.role_definition once per assignment.
        from awx.main.models.rbac import _field_names_for_old_rbac

        rds = [
            RoleDefinition.objects.get(name='Inventory Admin'),
            RoleDefinition.objects.get(name='Organization Admin'),
            RoleDefinition.objects.get(name='Project Admin'),
        ]

        # Stand-in assignment objects carrying only the role_definition_id the helper reads,
        # duplicated so the batch is larger than the number of distinct role definitions.
        class _Stub:
            def __init__(self, rd_id):
                self.role_definition_id = rd_id

        assignments = [_Stub(rd.id) for rd in rds] * 4

        with django_assert_num_queries(1):
            field_names = _field_names_for_old_rbac(assignments)

        assert field_names[rds[0].id] == 'admin_role'
        assert field_names[rds[1].id] == 'admin_role'

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
