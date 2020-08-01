import pytest
from unittest import mock
import os

from django.utils.timezone import now, timedelta

from awx.main.tasks import (
    RunProjectUpdate, RunInventoryUpdate,
    awx_isolated_heartbeat,
    isolated_manager
)
from awx.main.models import (
    ProjectUpdate, InventoryUpdate, InventorySource,
    Instance, InstanceGroup
)


@pytest.fixture
def scm_revision_file(tmpdir_factory):
    # Returns path to temporary testing revision file
    revision_file = tmpdir_factory.mktemp('revisions').join('revision.txt')
    with open(str(revision_file), 'w') as f:
        f.write('1234567890123456789012345678901234567890')
    return os.path.join(revision_file.dirname, 'revision.txt')


@pytest.mark.django_db
class TestDependentInventoryUpdate:

    def test_dependent_inventory_updates_is_called(self, scm_inventory_source, scm_revision_file):
        task = RunProjectUpdate()
        task.revision_path = scm_revision_file
        proj_update = scm_inventory_source.source_project.create_project_update()
        with mock.patch.object(RunProjectUpdate, '_update_dependent_inventories') as inv_update_mck:
            with mock.patch.object(RunProjectUpdate, 'release_lock'):
                task.post_run_hook(proj_update, 'successful')
                inv_update_mck.assert_called_once_with(proj_update, mock.ANY)

    def test_no_unwanted_dependent_inventory_updates(self, project, scm_revision_file):
        task = RunProjectUpdate()
        task.revision_path = scm_revision_file
        proj_update = project.create_project_update()
        with mock.patch.object(RunProjectUpdate, '_update_dependent_inventories') as inv_update_mck:
            with mock.patch.object(RunProjectUpdate, 'release_lock'):
                task.post_run_hook(proj_update, 'successful')
                assert not inv_update_mck.called

    def test_dependent_inventory_updates(self, scm_inventory_source):
        task = RunProjectUpdate()
        scm_inventory_source.scm_last_revision = ''
        proj_update = ProjectUpdate.objects.create(project=scm_inventory_source.source_project)
        with mock.patch.object(RunInventoryUpdate, 'run') as iu_run_mock:
            task._update_dependent_inventories(proj_update, [scm_inventory_source])
            assert InventoryUpdate.objects.count() == 1
            inv_update = InventoryUpdate.objects.first()
            iu_run_mock.assert_called_once_with(inv_update.id)
            assert inv_update.source_project_update_id == proj_update.pk

    def test_dependent_inventory_project_cancel(self, project, inventory):
        '''
        Test that dependent inventory updates exhibit good behavior on cancel
        of the source project update
        '''
        task = RunProjectUpdate()
        proj_update = ProjectUpdate.objects.create(project=project)

        kwargs = dict(
            source_project=project,
            source='scm',
            source_path='inventory_file',
            update_on_project_update=True,
            inventory=inventory
        )

        is1 = InventorySource.objects.create(name="test-scm-inv", **kwargs)
        is2 = InventorySource.objects.create(name="test-scm-inv2", **kwargs)

        def user_cancels_project(pk):
            ProjectUpdate.objects.all().update(cancel_flag=True)

        with mock.patch.object(RunInventoryUpdate, 'run') as iu_run_mock:
            iu_run_mock.side_effect = user_cancels_project
            task._update_dependent_inventories(proj_update, [is1, is2])
            # Verify that it bails after 1st update, detecting a cancel
            assert is2.inventory_updates.count() == 0
            iu_run_mock.assert_called_once()



class MockSettings:
    AWX_ISOLATED_PERIODIC_CHECK = 60
    CLUSTER_HOST_ID = 'tower_1'


@pytest.mark.django_db
class TestIsolatedManagementTask:

    @pytest.fixture
    def control_group(self):
        return InstanceGroup.objects.create(name='alpha')

    @pytest.fixture
    def control_instance(self, control_group):
        return control_group.instances.create(hostname='tower_1')

    @pytest.fixture
    def needs_updating(self, control_group):
        ig = InstanceGroup.objects.create(name='thepentagon', controller=control_group)
        inst = ig.instances.create(hostname='isolated', capacity=103)
        inst.last_isolated_check=now() - timedelta(seconds=MockSettings.AWX_ISOLATED_PERIODIC_CHECK)
        inst.save()
        return ig

    @pytest.fixture
    def just_updated(self, control_group):
        ig = InstanceGroup.objects.create(name='thepentagon', controller=control_group)
        inst = ig.instances.create(hostname='isolated', capacity=103)
        inst.last_isolated_check=now()
        inst.save()
        return inst

    @pytest.fixture
    def old_version(self, control_group):
        ig = InstanceGroup.objects.create(name='thepentagon', controller=control_group)
        inst = ig.instances.create(hostname='isolated-old', capacity=103)
        inst.save()
        return inst

    def test_takes_action(self, control_instance, needs_updating):
        original_isolated_instance = needs_updating.instances.all().first()
        with mock.patch('awx.main.tasks.settings', MockSettings()):
            with mock.patch.object(isolated_manager.IsolatedManager, 'health_check') as check_mock:
                awx_isolated_heartbeat()
        iso_instance = Instance.objects.get(hostname='isolated')
        call_args, _ = check_mock.call_args
        assert call_args[0][0] == iso_instance
        assert iso_instance.last_isolated_check > original_isolated_instance.last_isolated_check
        assert iso_instance.modified == original_isolated_instance.modified

    def test_does_not_take_action(self, control_instance, just_updated):
        with mock.patch('awx.main.tasks.settings', MockSettings()):
            with mock.patch.object(isolated_manager.IsolatedManager, 'health_check') as check_mock:
                awx_isolated_heartbeat()
        iso_instance = Instance.objects.get(hostname='isolated')
        check_mock.assert_not_called()
        assert iso_instance.capacity == 103
