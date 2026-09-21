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
def test_managed_image_in_global_ee_settings_not_cleaned(cleanup_patch, settings):
    """Images in GLOBAL_JOB_EXECUTION_ENVIRONMENTS should not be cleaned up"""
    settings.GLOBAL_JOB_EXECUTION_ENVIRONMENTS = [{'name': 'Managed EE', 'image': 'quay.io/managed/ee:latest'}]

    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/managed/ee:latest')
    ee.image = 'quay.io/new/image:v1'
    ee.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_managed_image_matching_control_plane_not_cleaned(cleanup_patch, settings):
    """Images matching CONTROL_PLANE_EXECUTION_ENVIRONMENT should not be cleaned up"""
    settings.CONTROL_PLANE_EXECUTION_ENVIRONMENT = 'quay.io/control/plane:latest'

    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/control/plane:latest')
    ee.image = 'quay.io/new/image:v1'
    ee.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_managed_ee_object_not_cleaned(cleanup_patch):
    """Images belonging to a managed=True EE object should not be cleaned up"""
    ExecutionEnvironment.objects.create(name='managed-ee', image='quay.io/foo/bar:latest', managed=True)

    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:latest')
    ee.image = 'quay.io/new/image:v1'
    ee.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_tag_to_digest_same_repo_not_cleaned(cleanup_patch):
    """When updating from tag to digest for the same repo, skip cleanup"""
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:latest')
    ee.image = 'quay.io/foo/bar@sha256:abc123def456'
    ee.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_digest_to_tag_same_repo_not_cleaned(cleanup_patch):
    """When updating from digest to tag for the same repo, skip cleanup"""
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar@sha256:abc123def456')
    ee.image = 'quay.io/foo/bar:latest'
    ee.save()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_different_tags_same_repo_is_cleaned(cleanup_patch):
    """Different tags for the same repo are genuinely different images and should be cleaned up"""
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:v1')
    ee.image = 'quay.io/foo/bar:v2'
    ee.save()

    cleanup_patch.delay.assert_called_once_with(remove_images=['quay.io/foo/bar:v1'])


@pytest.mark.django_db
def test_delete_ee_with_other_ee_sharing_repo_different_ref(cleanup_patch):
    """On delete, skip cleanup if another EE uses the same repo with a different ref form"""
    ExecutionEnvironment.objects.create(name='other-ee', image='quay.io/foo/bar@sha256:abc123')
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:latest')
    ee.delete()

    cleanup_patch.delay.assert_not_called()


@pytest.mark.django_db
def test_delete_ee_no_shared_repo_is_cleaned(cleanup_patch):
    """On delete, clean up when no other EE shares the repo"""
    ExecutionEnvironment.objects.create(name='other-ee', image='quay.io/different/repo:latest')
    ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar:latest')
    ee.delete()

    cleanup_patch.delay.assert_called_once_with(remove_images=['quay.io/foo/bar:latest'])
