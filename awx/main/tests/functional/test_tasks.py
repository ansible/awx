import pytest
from unittest import mock
import os

from awx.main.tasks import RunProjectUpdate, RunInventoryUpdate
from awx.main.models import ProjectUpdate, InventoryUpdate, InventorySource


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
        """
        Test that dependent inventory updates exhibit good behavior on cancel
        of the source project update
        """
        task = RunProjectUpdate()
        proj_update = ProjectUpdate.objects.create(project=project)

        kwargs = dict(source_project=project, source='scm', source_path='inventory_file', update_on_project_update=True, inventory=inventory)

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
