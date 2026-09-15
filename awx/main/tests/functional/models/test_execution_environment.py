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


@pytest.mark.django_db
def test_image_in_global_job_execution_environments_not_cleaned(cleanup_patch, settings):
    """AAP-89067: Images in GLOBAL_JOB_EXECUTION_ENVIRONMENTS should not be cleaned up"""
    settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS = [{'name': 'Test EE', 'image': 'quay.io/managed/ee:latest'}]

    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/managed/ee:latest')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_image_matching_control_plane_not_cleaned(cleanup_patch, settings):
    """AAP-89067: Images matching CONTROL_PLANE_EXECUTION_ENVIRONMENT should not be cleaned up"""
    settings.CONTROL_PLANE_EXECUTION_ENVIRONMENT = 'quay.io/control/plane:latest'

    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/control/plane:latest')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_image_same_repo_different_ref_not_cleaned(cleanup_patch):
    """AAP-89067: When another EE uses the same repo with different reference form (tag vs digest), skip cleanup"""
    # Create EE with digest reference
    ExecutionEnvironment.objects.create(name='other-ee', image='quay.io/foo/bar@sha256:abc123def456')

    # Create EE with tag reference and change it
    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:latest')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    # Should NOT clean up quay.io/foo/bar:latest because quay.io/foo/bar@sha256:... might be the same image
    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_image_different_repo_is_cleaned(cleanup_patch):
    """Images from completely different repositories should still be cleaned up"""
    ExecutionEnvironment.objects.create(name='other-ee', image='quay.io/different/repo:latest')

    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:latest')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    # Should clean up quay.io/foo/bar:latest because quay.io/different/repo is a different image
    cleanup_patch.delay.assert_called_once_with(remove_images=['quay.io/foo/bar:latest'])


@pytest.mark.django_db
def test_image_repo_extraction_with_digest(cleanup_patch):
    """Test that digest references are properly handled"""
    ExecutionEnvironment.objects.create(name='other-ee', image='quay.io/foo/bar:latest')

    execution_environment = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar@sha256:abc123def456')
    execution_environment.image = 'quay.io/new/image'
    execution_environment.save()

    # Should NOT clean up the digest reference because quay.io/foo/bar:latest might be the same image
    cleanup_patch.delay.assert_not_called()
