# Test for Constructed Inventory Cascading Sync Feature
# ANSTRAT-2626 / GitHub ansible/awx#13504
#
# This file should be added to: awx/main/tests/unit/test_task_manager.py
# Or run as a standalone test file

import pytest
from unittest import mock
from django.utils.timezone import now as tz_now

from awx.main.models import (
    Inventory,
    InventorySource,
    InventoryUpdate,
    Organization,
    Project,
    UnifiedJob,
)
from awx.main.scheduler.task_manager import TaskManager


@pytest.mark.django_db
class TestConstructedInventoryCascadingSync:
    """
    Test that constructed inventories trigger updates for input inventory sources
    that have update_on_launch=True
    """

    def test_gen_dep_for_constructed_inventory_with_update_on_launch(self):
        """
        Test that input inventory sources with update_on_launch=True are added as dependencies
        for the constructed inventory update task.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        # Create project
        project = Project.objects.create(
            name='Test Project',
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
        )

        # Create input inventory 1 with source (update_on_launch=True)
        inv_s1 = Inventory.objects.create(
            name='invS1',
            organization=org,
        )
        inv_s1_source = InventorySource.objects.create(
            name='invS1-source',
            inventory=inv_s1,
            source='scm',
            source_project=project,
            source_path='inventory1',
            update_on_launch=True,
            update_cache_timeout=0,
        )

        # Create input inventory 2 with source (update_on_launch=True)
        inv_s2 = Inventory.objects.create(
            name='invS2',
            organization=org,
        )
        inv_s2_source = InventorySource.objects.create(
            name='invS2-source',
            inventory=inv_s2,
            source='scm',
            source_project=project,
            source_path='inventory2',
            update_on_launch=True,
            update_cache_timeout=0,
        )

        # Create constructed inventory
        inv_c = Inventory.objects.create(
            name='InvC',
            organization=org,
            kind='constructed',
        )
        inv_c.input_inventories.add(inv_s1, inv_s2)

        # Create auto-created source for constructed inventory
        inv_c_source = InventorySource.objects.create(
            name='InvC-auto',
            inventory=inv_c,
            source='constructed',
            update_on_launch=True,
        )

        # Create inventory update task for the constructed inventory
        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_c_source,
            inventory=inv_c,
            source='constructed',
        )

        # Create task manager and test dependency generation
        tm = TaskManager()

        # Mock the should_update_again method to return True (needs update)
        with mock.patch.object(tm, 'should_update_again', return_value=True):
            dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Verify that dependencies were created for both input sources
        assert len(dependencies) == 2, f"Expected 2 dependencies, got {len(dependencies)}"

        # Verify the dependencies are inventory updates for the input sources
        dep_source_ids = [dep.inventory_source_id for dep in dependencies]
        assert inv_s1_source.id in dep_source_ids, "invS1-source should be in dependencies"
        assert inv_s2_source.id in dep_source_ids, "invS2-source should be in dependencies"

    def test_gen_dep_for_constructed_inventory_cache_timeout_honored(self):
        """
        Test that cache timeout is respected - recent updates are reused instead of creating new ones.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        # Create project
        project = Project.objects.create(
            name='Test Project',
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
        )

        # Create input inventory with source
        inv_s1 = Inventory.objects.create(name='invS1', organization=org)
        inv_s1_source = InventorySource.objects.create(
            name='invS1-source',
            inventory=inv_s1,
            source='scm',
            source_project=project,
            source_path='inventory1',
            update_on_launch=True,
            update_cache_timeout=300,  # 5 minutes
        )

        # Create a recent inventory update (within cache window)
        recent_update = InventoryUpdate.objects.create(
            inventory_source=inv_s1_source,
            inventory=inv_s1,
            source='scm',
            status='successful',
            finished=tz_now(),
        )

        # Create constructed inventory
        inv_c = Inventory.objects.create(name='InvC', organization=org, kind='constructed')
        inv_c.input_inventories.add(inv_s1)

        inv_c_source = InventorySource.objects.create(
            name='InvC-auto',
            inventory=inv_c,
            source='constructed',
        )

        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_c_source,
            inventory=inv_c,
            source='constructed',
        )

        # Test dependency generation
        tm = TaskManager()

        # Mock should_update_again to return False (within cache window)
        with mock.patch.object(tm, 'should_update_again', return_value=False):
            dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Should reuse the existing update (not create new one)
        assert len(dependencies) == 1, "Should reuse existing update"
        assert dependencies[0].id == recent_update.id, "Should return the recent update"

    def test_gen_dep_for_constructed_inventory_mixed_update_on_launch(self):
        """
        Test that only sources with update_on_launch=True are synced.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        project = Project.objects.create(
            name='Test Project',
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
        )

        # Input 1: update_on_launch=True
        inv_s1 = Inventory.objects.create(name='invS1', organization=org)
        inv_s1_source = InventorySource.objects.create(
            name='invS1-source',
            inventory=inv_s1,
            source='scm',
            source_project=project,
            update_on_launch=True,  # Should sync
        )

        # Input 2: update_on_launch=False
        inv_s2 = Inventory.objects.create(name='invS2', organization=org)
        _inv_s2_source = InventorySource.objects.create(
            name='invS2-source',
            inventory=inv_s2,
            source='scm',
            source_project=project,
            update_on_launch=False,  # Should NOT sync
        )

        # Constructed inventory
        inv_c = Inventory.objects.create(name='InvC', organization=org, kind='constructed')
        inv_c.input_inventories.add(inv_s1, inv_s2)

        inv_c_source = InventorySource.objects.create(
            name='InvC-auto',
            inventory=inv_c,
            source='constructed',
        )

        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_c_source,
            inventory=inv_c,
            source='constructed',
        )

        tm = TaskManager()
        with mock.patch.object(tm, 'should_update_again', return_value=True):
            dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Only invS1-source should be in dependencies
        assert len(dependencies) == 1, f"Expected 1 dependency, got {len(dependencies)}"
        assert dependencies[0].inventory_source_id == inv_s1_source.id

    def test_gen_dep_for_constructed_inventory_no_input_sources(self):
        """
        Test that constructed inventory with no input inventory sources doesn't break.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        # Constructed inventory with no inputs
        inv_c = Inventory.objects.create(name='InvC-Empty', organization=org, kind='constructed')

        inv_c_source = InventorySource.objects.create(
            name='InvC-auto',
            inventory=inv_c,
            source='constructed',
        )

        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_c_source,
            inventory=inv_c,
            source='constructed',
        )

        tm = TaskManager()
        dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Should return empty list (no dependencies)
        assert dependencies == [], "Should return empty list when no input inventories"

    def test_gen_dep_for_constructed_inventory_no_sources_on_inputs(self):
        """
        Test that input inventories with no sources don't cause errors.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        # Input inventory with no sources
        inv_s1 = Inventory.objects.create(name='invS1-NoSource', organization=org)

        # Constructed inventory
        inv_c = Inventory.objects.create(name='InvC', organization=org, kind='constructed')
        inv_c.input_inventories.add(inv_s1)

        inv_c_source = InventorySource.objects.create(
            name='InvC-auto',
            inventory=inv_c,
            source='constructed',
        )

        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_c_source,
            inventory=inv_c,
            source='constructed',
        )

        tm = TaskManager()
        dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Should return empty list (no sources to sync)
        assert dependencies == [], "Should handle input inventories with no sources"

    def test_gen_dep_for_normal_inventory_unchanged(self):
        """
        Test that normal (non-constructed) inventory behavior is unchanged.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        project = Project.objects.create(
            name='Test Project',
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
        )

        # Normal inventory with SCM source
        inv = Inventory.objects.create(name='Normal-Inv', organization=org)
        inv_source = InventorySource.objects.create(
            name='normal-source',
            inventory=inv,
            source='scm',
            source_project=project,
            update_on_launch=True,
        )

        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_source,
            inventory=inv,
            source='scm',
        )

        tm = TaskManager()

        # Mock get_or_create_project_update to return a project update
        mock_project_update = [mock.Mock(spec=UnifiedJob)]
        with mock.patch.object(tm, 'get_or_create_project_update', return_value=mock_project_update):
            dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Should return project dependencies (existing behavior)
        assert len(dependencies) == 1, "Should return project dependency for SCM source"
        assert dependencies == mock_project_update

    def test_gen_dep_for_constructed_with_scm_source(self):
        """
        Test that constructed inventory SCM sources still create project dependencies.
        """
        # Create organization
        org = Organization.objects.create(name='Test Org')

        project = Project.objects.create(
            name='Test Project',
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
        )

        # Constructed inventory with SCM source (edge case)
        inv_c = Inventory.objects.create(name='InvC', organization=org, kind='constructed')

        inv_c_source = InventorySource.objects.create(
            name='InvC-scm-source',
            inventory=inv_c,
            source='scm',  # SCM source on constructed inventory
            source_project=project,
        )

        inv_update = InventoryUpdate.objects.create(
            inventory_source=inv_c_source,
            inventory=inv_c,
            source='scm',
        )

        tm = TaskManager()

        # Mock get_or_create_project_update
        mock_project_update = [mock.Mock(spec=UnifiedJob)]
        with mock.patch.object(tm, 'get_or_create_project_update', return_value=mock_project_update):
            dependencies = tm.gen_dep_for_inventory_update(inv_update)

        # Should handle both SCM project dependency AND input inventory dependencies
        # In this case, only project dependency since source is 'scm', not 'constructed'
        assert len(dependencies) == 1, "Should return project dependency for SCM source"
