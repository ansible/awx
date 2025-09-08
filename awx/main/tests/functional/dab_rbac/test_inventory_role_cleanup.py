# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.

import pytest
from django.contrib.contenttypes.models import ContentType

from awx.main.models import Inventory, Organization, User
from awx.main.tasks.system import delete_inventory
from ansible_base.rbac.models import RoleUserAssignment, ObjectRole, RoleDefinition


@pytest.mark.django_db
def test_role_assignment_deleted_with_inventory_sync(inventory, alice):
    """Test role assignments are deleted when inventory is deleted synchronously."""
    # Get or create the Inventory Admin role definition
    try:
        inv_rd = RoleDefinition.objects.get(name='Inventory Admin')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        inv_rd = RoleDefinition.objects.create(name='Inventory Admin', description='Can manage inventory', content_type=ct)

    # Create a role assignment for the inventory
    assignment = inv_rd.give_permission(alice, inventory)

    # Verify assignment exists
    assert RoleUserAssignment.objects.filter(
        user=alice, object_id=str(inventory.pk), role_definition=inv_rd
    ).exists(), "Role assignment should exist before inventory deletion"

    # Verify ObjectRole exists
    ct = ContentType.objects.get_for_model(inventory)
    assert ObjectRole.objects.filter(
        content_type=ct, object_id=str(inventory.pk), role_definition=inv_rd
    ).exists(), "ObjectRole should exist before inventory deletion"

    # Store IDs for verification after deletion
    inventory_id = str(inventory.pk)
    user_id = alice.pk

    # Delete inventory synchronously
    inventory.delete()

    # Verify role assignment is deleted
    assert not RoleUserAssignment.objects.filter(
        user_id=user_id, object_id=inventory_id, role_definition=inv_rd
    ).exists(), "Role assignment should be deleted after inventory deletion"

    # Verify ObjectRole is deleted
    assert not ObjectRole.objects.filter(
        content_type=ct, object_id=inventory_id, role_definition=inv_rd
    ).exists(), "ObjectRole should be deleted after inventory deletion"


@pytest.mark.django_db
def test_role_assignment_deleted_with_inventory_async(inventory, alice):
    """Test role assignments are deleted when inventory is deleted via async task."""
    # Get or create the Inventory Admin role definition
    try:
        inv_rd = RoleDefinition.objects.get(name='Inventory Admin')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        inv_rd = RoleDefinition.objects.create(name='Inventory Admin', description='Can manage inventory', content_type=ct)

    # Create a role assignment for the inventory
    assignment = inv_rd.give_permission(alice, inventory)

    inventory_id = inventory.pk
    user_id = alice.pk

    # Verify assignment exists before deletion
    assert RoleUserAssignment.objects.filter(
        user=alice, object_id=str(inventory_id), role_definition=inv_rd
    ).exists(), "Role assignment should exist before async deletion"

    # Mark as pending deletion and call async task directly
    inventory.pending_deletion = True
    inventory.save()

    # Call the actual deletion task (runs synchronously in tests)
    delete_inventory(inventory_id, user_id)

    # Verify role assignment is deleted
    assert not RoleUserAssignment.objects.filter(
        user_id=user_id, object_id=str(inventory_id), role_definition=inv_rd
    ).exists(), "Role assignment should be deleted after async inventory deletion"


@pytest.mark.django_db
def test_multiple_role_assignments_cleanup(inventory, alice, bob):
    """Test multiple role assignments for same inventory are all deleted."""
    # Get or create role definitions
    try:
        inv_rd = RoleDefinition.objects.get(name='Inventory Admin')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        inv_rd = RoleDefinition.objects.create(name='Inventory Admin', description='Can manage inventory', content_type=ct)

    try:
        use_rd = RoleDefinition.objects.get(name='Inventory Use')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        use_rd = RoleDefinition.objects.create(name='Inventory Use', description='Can use inventory', content_type=ct)

    # Create multiple role assignments
    assignment1 = inv_rd.give_permission(alice, inventory)
    assignment2 = use_rd.give_permission(bob, inventory)

    inventory_id = str(inventory.pk)

    # Verify both assignments exist
    assignments_count = RoleUserAssignment.objects.filter(object_id=inventory_id).count()
    assert assignments_count == 2, f"Should have 2 role assignments, but found {assignments_count}"

    # Delete inventory
    inventory.delete()

    # Verify all assignments are deleted
    remaining_assignments = RoleUserAssignment.objects.filter(object_id=inventory_id).count()
    assert remaining_assignments == 0, f"All role assignments should be deleted, but found {remaining_assignments}"


@pytest.mark.django_db
def test_other_inventory_assignments_unaffected(inventory, alice, organization):
    """Test that deleting one inventory doesn't affect role assignments for other inventories."""
    # Create second inventory
    inventory2 = Inventory.objects.create(name='Test Inventory 2', organization=organization)

    # Get or create role definition
    try:
        inv_rd = RoleDefinition.objects.get(name='Inventory Admin')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        inv_rd = RoleDefinition.objects.create(name='Inventory Admin', description='Can manage inventory', content_type=ct)

    # Create assignments for both inventories
    assignment1 = inv_rd.give_permission(alice, inventory)
    assignment2 = inv_rd.give_permission(alice, inventory2)

    inventory1_id = str(inventory.pk)
    inventory2_id = str(inventory2.pk)

    # Verify both assignments exist
    assert RoleUserAssignment.objects.filter(user=alice, object_id=inventory1_id, role_definition=inv_rd).exists(), "First inventory assignment should exist"

    assert RoleUserAssignment.objects.filter(user=alice, object_id=inventory2_id, role_definition=inv_rd).exists(), "Second inventory assignment should exist"

    # Delete first inventory
    inventory.delete()

    # Verify first assignment deleted, second preserved
    assert not RoleUserAssignment.objects.filter(
        user=alice, object_id=inventory1_id, role_definition=inv_rd
    ).exists(), "First inventory assignment should be deleted"

    assert RoleUserAssignment.objects.filter(
        user=alice, object_id=inventory2_id, role_definition=inv_rd
    ).exists(), "Second inventory assignment should still exist"


@pytest.mark.django_db
def test_inventory_deletion_with_no_assignments(inventory):
    """Test inventory deletion works normally when there are no role assignments."""
    inventory_id = inventory.pk

    # Verify no role assignments exist
    assert RoleUserAssignment.objects.filter(object_id=str(inventory_id)).count() == 0, "Should have no role assignments initially"

    # Delete inventory - should work without errors
    inventory.delete()

    # Verify inventory is deleted
    assert not Inventory.objects.filter(pk=inventory_id).exists(), "Inventory should be deleted"


@pytest.mark.django_db
def test_aap_52518_exact_reproduction(organization):
    """Test the exact scenario described in AAP-52518 Jira ticket."""
    # Step 1: Create an Organization and a User
    user = User.objects.create(username='testuser', email='testuser@example.com', is_active=True)

    # Step 2: Create a Controller inventory in that org
    inventory = Inventory.objects.create(name='Test Controller Inventory', organization=organization, description='Test inventory for AAP-52518')

    # Step 3: Create a role user assignment for the user to become Inventory Admin
    try:
        inv_admin_role = RoleDefinition.objects.get(name='Inventory Admin')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        inv_admin_role = RoleDefinition.objects.create(name='Inventory Admin', description='Can administer inventory', content_type=ct)

    # Give the user Inventory Admin permission on this inventory
    role_assignment = inv_admin_role.give_permission(user, inventory)

    # Verify the role assignment was created
    assignment_id = role_assignment.id
    assert RoleUserAssignment.objects.filter(id=assignment_id).exists(), "Role assignment should exist after creation"

    # Store data for verification after deletion
    inventory_id = inventory.pk
    user_id = user.pk

    # Step 4: Delete the inventory
    inventory.delete()

    # Step 5: Check the role_user_assignments list - should be empty
    assignments_after = RoleUserAssignment.objects.filter(user_id=user_id, object_id=str(inventory_id)).count()
    assert assignments_after == 0, "Role assignment should be completely removed after inventory deletion"

    # Additional verification: Ensure no orphaned records exist
    assert not RoleUserAssignment.objects.filter(
        user_id=user_id, object_id=str(inventory_id)
    ).exists(), "No role assignments should exist for deleted inventory"

    # Verify ObjectRole was also cleaned up
    ct = ContentType.objects.get_for_model(Inventory)
    assert not ObjectRole.objects.filter(content_type=ct, object_id=str(inventory_id)).exists(), "No ObjectRole should exist for deleted inventory"


@pytest.mark.django_db
def test_multiple_users_same_inventory_cleanup(inventory):
    """Test cleanup works when multiple users have roles on the same inventory."""
    # Create additional users
    user2 = User.objects.create(username='testuser2', email='test2@example.com')
    user3 = User.objects.create(username='testuser3', email='test3@example.com')

    # Create role definitions
    try:
        admin_role = RoleDefinition.objects.get(name='Inventory Admin')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        admin_role = RoleDefinition.objects.create(name='Inventory Admin', description='Can administer inventory', content_type=ct)

    try:
        use_role = RoleDefinition.objects.get(name='Inventory Use')
    except RoleDefinition.DoesNotExist:
        ct = ContentType.objects.get_for_model(Inventory)
        use_role = RoleDefinition.objects.create(name='Inventory Use', description='Can use inventory', content_type=ct)

    # Assign different roles to different users
    assignment1 = admin_role.give_permission(user2, inventory)
    assignment2 = admin_role.give_permission(user3, inventory)
    assignment3 = use_role.give_permission(user3, inventory)

    inventory_id = inventory.pk

    # Verify all assignments exist
    assignments_before = RoleUserAssignment.objects.filter(object_id=str(inventory_id)).count()
    assert assignments_before == 3, "Should have 3 role assignments"

    # Delete inventory
    inventory.delete()

    # Verify all assignments are cleaned up
    assignments_after = RoleUserAssignment.objects.filter(object_id=str(inventory_id)).count()
    assert assignments_after == 0, "All assignments should be deleted"
