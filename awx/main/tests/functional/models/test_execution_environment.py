import pytest

from awx.main.models.execution_environments import ExecutionEnvironment


@pytest.mark.django_db
def test_image_unchanged_no_delete_task(mocker):
    """When an irrelevant EE field is changed, we do not run the image cleanup task"""
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    execution_environment.description = 'foobar'
    with mocker.patch('awx.main.signals.handle_removed_image') as p1:
        with mocker.patch('awx.main.signals.cleanup_images_and_files_execution_nodes') as p2:
            execution_environment.save()
            p1.assert_not_called()
            p2.assert_not_called()


@pytest.mark.django_db
def test_image_unchanged_no_delete_task(mocker):
    """When an irrelevant EE field is changed, we do not run the image cleanup task"""
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    execution_environment.image = 'quay.io/new/image'
    with mocker.patch('awx.main.signals.handle_removed_image'):
        with mocker.patch('awx.main.signals.cleanup_images_and_files_execution_nodes'):
            execution_environment.save()
            from awx.main.signals import handle_removed_image, cleanup_images_and_files_execution_nodes

            handle_removed_image.delay.assert_called_once_with(remove_images='quay.io/foo/bar')
            cleanup_images_and_files_execution_nodes.delay.assert_called_once_with(remove_images='quay.io/foo/bar')
