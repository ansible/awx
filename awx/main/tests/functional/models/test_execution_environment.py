import pytest

from awx.main.models.execution_environments import ExecutionEnvironment


@pytest.fixture
def cleanup_patch(mocker):
    return mocker.patch('awx.main.signals.handle_removed_image')


@pytest.mark.django_db
def test_image_unchanged_no_delete_task(cleanup_patch):
    """When an irrelevant EE field is changed, we do not run the image cleanup task"""
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    execution_environment.description = 'foobar'
    execution_environment.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_image_changed_creates_delete_task(cleanup_patch):
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    cleanup_patch.delay.assert_called_once_with(remove_images=['quay.io/foo/bar'])


@pytest.mark.django_db
def test_image_still_in_use(cleanup_patch):
    """When an image is still in use by another EE, we do not clean it up"""
    ExecutionEnvironment.objects.create(name='unrelated-ee', image='quay.io/foo/bar')
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_image_deletion_creates_delete_task(cleanup_patch):
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
    execution_environment.delete()

    cleanup_patch.delay.assert_called_once_with(remove_images=['quay.io/foo/bar'])
