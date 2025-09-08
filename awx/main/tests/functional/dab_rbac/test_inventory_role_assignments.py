# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.

import pytest

from awx.main.models import Inventory, User
from awx.main.tasks.system import delete_inventory
from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment


@pytest.mark.django_db
def test_inventory_role_assignments_deleted_sync(inventory, alice, setup_managed_roles):
    """Test role assignments are properly cleaned up when inventory is deleted synchronously."""
    # Get the managed Inventory Admin role definition
    inv_rd = RoleDefinition.objects.get(name='Inventory Admin')

    # Create a role assignment for the inventory
    inv_rd.give_permission(alice, inventory)

    # Verify assignment exists
    assert RoleUserAssignment.objects.filter(user=alice, object_id=str(inventory.pk), role_definition=inv_rd).exists()

    inventory_id = str(inventory.pk)

    # Delete inventory synchronously
    inventory.delete()

    # Verify role assignment is cleaned up
    assert not RoleUserAssignment.objects.filter(object_id=inventory_id, role_definition=inv_rd).exists()


@pytest.mark.django_db
def test_inventory_role_assignments_deleted_async(inventory, alice, setup_managed_roles):
    """Test role assignments are properly cleaned up via schedule_deletion."""
    from unittest.mock import patch

    # Get the managed Inventory Admin role definition
    inv_rd = RoleDefinition.objects.get(name='Inventory Admin')

    # Create a role assignment for the inventory
    inv_rd.give_permission(alice, inventory)

    inventory_id = inventory.pk
    user_id = alice.pk

    # Verify assignment exists before deletion
    assert RoleUserAssignment.objects.filter(user=alice, object_id=str(inventory_id), role_definition=inv_rd).exists()

    # Mock the WebSocket notification to avoid Redis dependency
    with patch('awx.main.tasks.system.emit_channel_notification'):
        # Call delete_inventory directly (simulating Celery task)
        delete_inventory(inventory_id, user_id)

    # Verify role assignment is cleaned up
    assert not RoleUserAssignment.objects.filter(user_id=user_id, object_id=str(inventory_id), role_definition=inv_rd).exists()


@pytest.mark.django_db
def test_multiple_inventory_role_assignments_cleanup(inventory, alice, bob, setup_managed_roles):
    """Test multiple role assignments are cleaned up when inventory is deleted."""
    # Get managed role definitions
    inv_rd = RoleDefinition.objects.get(name='Inventory Admin')
    use_rd = RoleDefinition.objects.get(name='Inventory Use')

    # Create multiple role assignments
    inv_rd.give_permission(alice, inventory)
    use_rd.give_permission(bob, inventory)

    inventory_id = str(inventory.pk)

    # Verify assignments exist
    assert RoleUserAssignment.objects.filter(object_id=inventory_id).count() == 2

    # Delete inventory
    inventory.delete()

    # Verify all assignments are cleaned up
    assert RoleUserAssignment.objects.filter(object_id=inventory_id).count() == 0


@pytest.mark.django_db
def test_aap_52518_reproduction(organization, setup_managed_roles):
    """Test the exact scenario described in AAP-52518."""
    # Create user and inventory per Jira scenario
    user = User.objects.create(username='testuser', email='testuser@example.com', is_active=True)
    inventory = Inventory.objects.create(name='Test Controller Inventory', organization=organization, description='Test inventory for AAP-52518')

    # Step 3: Create role user assignment for user to become Inventory Admin
    inv_admin_role = RoleDefinition.objects.get(name='Inventory Admin')
    inv_admin_role.give_permission(user, inventory)

    # Verify assignment was created
    assert RoleUserAssignment.objects.filter(user=user, object_id=str(inventory.pk), role_definition=inv_admin_role).exists()

    inventory_id = inventory.pk
    user_id = user.pk

    # Step 4: Delete the inventory
    inventory.delete()

    # Step 5: Verify no orphaned role assignments remain
    assert RoleUserAssignment.objects.filter(user_id=user_id, object_id=str(inventory_id)).count() == 0
