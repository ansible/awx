"""Unit tests for adoption hook invocation logic.

Tests the conditions, artifact validation, and type checking without
requiring database or EE integration.
"""

from unittest.mock import Mock

from awx.main.exceptions import PostRunError
from awx.main.models.jobs import Job
from awx.main.models.projects import ProjectUpdate
from awx.main.models.inventory import InventoryUpdate
from awx.main.tasks.adoption import (
    should_invoke_adoption_hook,
    _validate_adoption_artifacts,
    invoke_adoption_hooks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_job(job_class, job_id=1, inventory_id=None):
    """Create a mock job instance of the specified type."""
    job = Mock(spec=job_class)
    job.id = job_id
    if job_class == Job:
        # Use configure_mock to ensure inventory_id is handled correctly
        job.inventory_id = inventory_id
        # Mock the __class__ attribute for isinstance checks
        job.__class__ = job_class
    else:
        job.__class__ = job_class
    return job


# ---------------------------------------------------------------------------
# should_invoke_adoption_hook
# ---------------------------------------------------------------------------


def test_hook_skipped_if_status_not_successful():
    """Don't invoke hook if job status is not 'successful'."""
    job = _make_mock_job(InventoryUpdate)

    assert should_invoke_adoption_hook(job, 'failed') is False
    assert should_invoke_adoption_hook(job, 'error') is False
    assert should_invoke_adoption_hook(job, 'canceled') is False
    assert should_invoke_adoption_hook(job, 'pending') is False


def test_hook_invoked_for_inventory_update_on_success():
    """Invoke hook for InventoryUpdate on successful status."""
    job = _make_mock_job(InventoryUpdate)
    assert should_invoke_adoption_hook(job, 'successful') is True


def test_hook_invoked_for_project_update_on_success():
    """Invoke hook for ProjectUpdate on successful status."""
    job = _make_mock_job(ProjectUpdate)
    assert should_invoke_adoption_hook(job, 'successful') is True


def test_hook_invoked_for_job_only_with_inventory():
    """Invoke hook for Job only if it has inventory_id."""
    # Job with inventory
    job_with_inv = _make_mock_job(Job, inventory_id=5)
    assert should_invoke_adoption_hook(job_with_inv, 'successful') is True

    # Job without inventory
    job_no_inv = _make_mock_job(Job, inventory_id=None)
    assert should_invoke_adoption_hook(job_no_inv, 'successful') is False


def test_hook_skipped_for_unknown_job_type():
    """Don't invoke hook for unknown job types."""
    unknown_job = Mock()
    unknown_job.__class__.__name__ = 'UnknownJob'

    assert should_invoke_adoption_hook(unknown_job, 'successful') is False


# ---------------------------------------------------------------------------
# _validate_adoption_artifacts
# ---------------------------------------------------------------------------


def test_inventory_update_validates_output_json_exists(tmp_path):
    """InventoryUpdate requires output.json to exist."""
    job = _make_mock_job(InventoryUpdate)

    valid, error = _validate_adoption_artifacts(job, str(tmp_path))
    assert valid is False
    assert 'output.json not found' in error


def test_inventory_update_validates_output_json_readable(tmp_path):
    """Verify output.json is readable."""
    import os

    job = _make_mock_job(InventoryUpdate)

    # Create artifacts directory with output.json
    artifacts_dir = tmp_path / 'artifacts' / str(job.id)
    artifacts_dir.mkdir(parents=True)
    output_file = artifacts_dir / 'output.json'
    output_file.write_text('{}')

    # Make it unreadable
    os.chmod(str(output_file), 0o000)

    try:
        valid, error = _validate_adoption_artifacts(job, str(tmp_path))
        assert valid is False
        assert 'not readable' in error
    finally:
        # Restore permissions for cleanup
        os.chmod(str(output_file), 0o644)


def test_inventory_update_accepts_valid_artifacts(tmp_path):
    """Accept valid InventoryUpdate artifacts."""
    job = _make_mock_job(InventoryUpdate)

    # Create artifacts directory with readable output.json
    artifacts_dir = tmp_path / 'artifacts' / str(job.id)
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / 'output.json').write_text('{"all": {"hosts": {}}}')

    valid, error = _validate_adoption_artifacts(job, str(tmp_path))
    assert valid is True
    assert error is None


def test_project_update_validation_passes(tmp_path):
    """ProjectUpdate doesn't require specific artifacts."""
    job = _make_mock_job(ProjectUpdate)

    valid, error = _validate_adoption_artifacts(job, str(tmp_path))
    assert valid is True
    assert error is None


def test_job_validation_passes(tmp_path):
    """Job doesn't require specific artifacts."""
    job = _make_mock_job(Job)

    valid, error = _validate_adoption_artifacts(job, str(tmp_path))
    assert valid is True
    assert error is None


def test_unknown_type_validation_passes(tmp_path):
    """Unknown job types pass validation."""
    job = Mock()

    valid, error = _validate_adoption_artifacts(job, str(tmp_path))
    assert valid is True
    assert error is None


# ---------------------------------------------------------------------------
# invoke_adoption_hooks
# ---------------------------------------------------------------------------


def test_hook_skipped_if_should_not_invoke():
    """Skip hook execution if should_invoke returns False."""
    job = _make_mock_job(Job, inventory_id=None)
    callback = Mock()

    hook_succeeded, error = invoke_adoption_hooks(job, callback, '/tmp', 'successful')

    assert hook_succeeded is True
    assert error is None


def test_hook_fails_if_artifact_validation_fails(tmp_path):
    """Fail hook invocation if artifact validation fails."""
    job = _make_mock_job(InventoryUpdate)
    callback = Mock()

    hook_succeeded, error = invoke_adoption_hooks(job, callback, str(tmp_path), 'successful')

    assert hook_succeeded is False
    assert 'output.json not found' in error['explanation']


def test_hook_skipped_on_failed_status():
    """Skip hook if job status is failed."""
    job = _make_mock_job(InventoryUpdate)
    callback = Mock()

    hook_succeeded, error = invoke_adoption_hooks(job, callback, '/tmp', 'failed')

    assert hook_succeeded is True
    assert error is None


def test_hook_fails_if_task_class_not_available():
    """Fail gracefully if job._get_task_class() raises NotImplementedError."""
    job = _make_mock_job(ProjectUpdate)
    job._get_task_class.side_effect = NotImplementedError()
    callback = Mock()
    job.refresh_from_db = Mock()

    # Should skip hook and return True (no error)
    hook_succeeded, error = invoke_adoption_hooks(job, callback, '/tmp', 'successful')

    assert hook_succeeded is True
    assert error is None


def test_hook_fails_if_task_class_has_no_post_run_hook():
    """Handle case where task class exists but has no post_run_hook."""
    job = _make_mock_job(ProjectUpdate)
    task_class = Mock()
    task_class.__name__ = 'FakeTask'
    # Simulate hasattr returning False
    del task_class.post_run_hook
    job._get_task_class.return_value = task_class
    callback = Mock()
    job.refresh_from_db = Mock()

    # Should skip hook and return True (no error)
    hook_succeeded, error = invoke_adoption_hooks(job, callback, '/tmp', 'successful')

    assert hook_succeeded is True
    assert error is None


def test_hook_captures_generic_exception():
    """Capture generic exceptions from post_run_hook."""
    job = _make_mock_job(ProjectUpdate)
    task_class = Mock()
    task_class.__name__ = 'RunProjectUpdate'
    task_class.return_value.post_run_hook.side_effect = ValueError('Test error')
    job._get_task_class.return_value = task_class
    callback = Mock()
    job.refresh_from_db = Mock()
    job.job_env = None

    hook_succeeded, error = invoke_adoption_hooks(job, callback, '/tmp', 'successful')

    assert hook_succeeded is False
    assert 'ValueError' in error['explanation']
    assert 'traceback' in error
    assert error['explanation'].startswith('Adoption hook failed')


def test_hook_captures_post_run_error():
    """Handle PostRunError specially with status override."""
    job = _make_mock_job(ProjectUpdate)
    task_class = Mock()
    task_class.__name__ = 'RunProjectUpdate'
    post_run_error = PostRunError('Custom error message')
    post_run_error.status = 'failed'
    post_run_error.tb = 'traceback content'
    task_class.return_value.post_run_hook.side_effect = post_run_error
    job._get_task_class.return_value = task_class
    callback = Mock()
    job.refresh_from_db = Mock()
    job.job_env = None

    hook_succeeded, error = invoke_adoption_hooks(job, callback, '/tmp', 'successful')

    assert hook_succeeded is False
    assert error['explanation'] == 'Custom error message'
    assert error['status_override'] == 'failed'
    assert error['traceback'] == 'traceback content'


def test_hook_hands_private_data_dir_to_the_task_without_writing_job_env(tmp_path):
    """The hook gets the adoption directory from the task, so job_env, which can hold the
    whole host map, is neither read nor written."""
    job = _make_mock_job(ProjectUpdate)
    job.job_env = {'ORIGINAL': 'value'}
    task_class = Mock()
    task_class.__name__ = 'RunProjectUpdate'
    job._get_task_class.return_value = task_class
    job.refresh_from_db = Mock()
    job.save = Mock()

    hook_succeeded, _ = invoke_adoption_hooks(job, Mock(), str(tmp_path), 'successful')

    assert hook_succeeded is True
    assert task_class.return_value.private_data_dir == str(tmp_path)
    assert job.job_env == {'ORIGINAL': 'value'}
    job.refresh_from_db.assert_not_called()
    job.save.assert_not_called()


def _run_job_hook(tmp_path, task_private_data_dir=None, job_env_dir=None):
    """Run RunJob.post_run_hook with the fact cache on and return the finish_fact_cache mock."""
    from unittest.mock import patch
    from awx.main.tasks import jobs

    job = _make_mock_job(Job, inventory_id=1)
    job.inventory.kind = 'static'
    job.job_env = {'AWX_PRIVATE_DATA_DIR': job_env_dir} if job_env_dir else {}
    task = jobs.RunJob()
    task.runner_callback = Mock(artifacts_processed=True)
    task.should_use_fact_cache = lambda: True
    if task_private_data_dir:
        task.private_data_dir = task_private_data_dir

    with patch.object(jobs, 'finish_fact_cache') as finish_fact_cache:
        task.post_run_hook(job, 'successful')
    return job, finish_fact_cache


def test_run_job_hook_prefers_the_task_private_data_dir(tmp_path):
    """Adoption names its own directory, and job_env is not read for it."""
    job, finish_fact_cache = _run_job_hook(tmp_path, task_private_data_dir=str(tmp_path), job_env_dir='/gone')

    job.refresh_from_db.assert_not_called()
    assert finish_fact_cache.call_args[1]['artifacts_dir'].startswith(str(tmp_path))


def test_run_job_hook_falls_back_to_job_env_on_a_normal_run(tmp_path):
    """A normal run sets self.private_data_dir only after the hook, so job_env stays the source."""
    job, finish_fact_cache = _run_job_hook(tmp_path, job_env_dir=str(tmp_path))

    job.refresh_from_db.assert_called_once_with(fields=['job_env'])
    assert finish_fact_cache.call_args[1]['artifacts_dir'].startswith(str(tmp_path))
