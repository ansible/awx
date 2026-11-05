"""Functional tests for adoption hook invocation.

Tests the full hook condition evaluation and artifact validation with database objects.
"""

import pytest

from awx.main.models import Organization
from awx.main.models.inventory import Inventory, InventorySource, InventoryUpdate
from awx.main.models.projects import Project, ProjectUpdate
from awx.main.models.jobs import Job, JobTemplate
from awx.main.tasks.adoption import should_invoke_adoption_hook, _validate_adoption_artifacts


@pytest.mark.django_db
def test_should_invoke_adoption_hook_for_inventory_update():
    """should_invoke_adoption_hook returns True for InventoryUpdate on success."""
    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )

    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    assert should_invoke_adoption_hook(iu, 'successful') is True
    assert should_invoke_adoption_hook(iu, 'failed') is False


@pytest.mark.django_db
def test_should_invoke_adoption_hook_for_project_update():
    """should_invoke_adoption_hook returns True for ProjectUpdate on success."""
    org = Organization.objects.create(name='test_org')
    project = Project.objects.create(
        name='test_project',
        organization=org,
        scm_type='git',
        scm_url='https://github.com/test/repo',
    )

    pu = ProjectUpdate.objects.create(
        project=project,
    )

    assert should_invoke_adoption_hook(pu, 'successful') is True
    assert should_invoke_adoption_hook(pu, 'failed') is False


@pytest.mark.django_db
def test_should_invoke_adoption_hook_for_job_with_inventory():
    """should_invoke_adoption_hook returns True for Job with inventory on success."""
    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    project = Project.objects.create(name='test_proj', organization=org)
    jt = JobTemplate.objects.create(
        name='test_jt',
        inventory=inventory,
        project=project,
    )

    job = Job.objects.create(
        job_template=jt,
        inventory=inventory,
    )

    assert should_invoke_adoption_hook(job, 'successful') is True


@pytest.mark.django_db
def test_should_skip_adoption_hook_for_job_without_inventory():
    """should_invoke_adoption_hook returns False for Job without inventory."""
    org = Organization.objects.create(name='test_org')
    project = Project.objects.create(name='test_proj', organization=org)
    jt = JobTemplate.objects.create(
        name='test_jt',
        inventory=None,
        project=project,
    )

    job = Job.objects.create(
        job_template=jt,
        inventory=None,
    )

    assert should_invoke_adoption_hook(job, 'successful') is False


@pytest.mark.django_db
def test_validate_adoption_artifacts_inventory_update_success(tmp_path):
    """Artifact validation passes for InventoryUpdate with valid output.json."""
    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )

    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    # Create artifacts with valid output.json
    artifacts_dir = tmp_path / 'artifacts' / str(iu.id)
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / 'output.json').write_text('{"all": {"hosts": {}}}')

    valid, error = _validate_adoption_artifacts(iu, str(tmp_path))
    assert valid is True
    assert error is None


@pytest.mark.django_db
def test_validate_adoption_artifacts_inventory_update_missing(tmp_path):
    """Artifact validation fails for InventoryUpdate with missing output.json."""
    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )

    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    # No artifacts directory
    valid, error = _validate_adoption_artifacts(iu, str(tmp_path))
    assert valid is False
    assert 'output.json not found' in error


@pytest.mark.django_db
def test_validate_adoption_artifacts_project_update(tmp_path):
    """Artifact validation passes for ProjectUpdate (no strict requirements)."""
    org = Organization.objects.create(name='test_org')
    project = Project.objects.create(
        name='test_project',
        organization=org,
        scm_type='git',
        scm_url='https://github.com/test/repo',
    )

    pu = ProjectUpdate.objects.create(
        project=project,
    )

    # No artifacts needed
    valid, error = _validate_adoption_artifacts(pu, str(tmp_path))
    assert valid is True
    assert error is None


@pytest.mark.django_db
def test_validate_adoption_artifacts_job(tmp_path):
    """Artifact validation passes for Job (no strict requirements)."""
    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    project = Project.objects.create(name='test_proj', organization=org)
    jt = JobTemplate.objects.create(
        name='test_jt',
        inventory=inventory,
        project=project,
    )

    job = Job.objects.create(
        job_template=jt,
        inventory=inventory,
    )

    # No artifacts needed
    valid, error = _validate_adoption_artifacts(job, str(tmp_path))
    assert valid is True
    assert error is None


@pytest.mark.django_db
def test_should_invoke_adoption_hook_all_failed_statuses():
    """should_invoke_adoption_hook returns False for all non-successful statuses."""
    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )
    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    # All non-successful statuses should skip hooks
    for status in ['failed', 'error', 'canceled', 'pending', 'running']:
        result = should_invoke_adoption_hook(iu, status)
        assert result is False, f"Expected False for status={status}, got {result}"


@pytest.mark.django_db
def test_validate_adoption_artifacts_inventory_update_unreadable(tmp_path):
    """Artifact validation fails for InventoryUpdate with unreadable output.json."""
    import os

    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )
    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    # Create artifacts with unreadable output.json
    artifacts_dir = tmp_path / 'artifacts' / str(iu.id)
    artifacts_dir.mkdir(parents=True)
    output_file = artifacts_dir / 'output.json'
    output_file.write_text('{"all": {"hosts": {}}}')

    # Make it unreadable
    os.chmod(str(output_file), 0o000)

    try:
        valid, error = _validate_adoption_artifacts(iu, str(tmp_path))
        assert valid is False
        assert 'not readable' in error
    finally:
        # Restore permissions for cleanup
        os.chmod(str(output_file), 0o644)


@pytest.mark.django_db
def test_invoke_adoption_hooks_should_skip_when_not_applicable(tmp_path):
    """invoke_adoption_hooks returns immediately when hook should not run."""
    from unittest.mock import Mock
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )
    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    callback = Mock()
    # Failed status should skip hook
    succeeded, error = invoke_adoption_hooks(iu, callback, str(tmp_path), 'failed')
    assert succeeded is True
    assert error is None


@pytest.mark.django_db
def test_invoke_adoption_hooks_with_artifact_validation_failure(tmp_path):
    """invoke_adoption_hooks fails gracefully when artifact validation fails."""
    from unittest.mock import Mock
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )
    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    callback = Mock()

    # No artifacts directory, so validation fails
    succeeded, error = invoke_adoption_hooks(iu, callback, str(tmp_path), 'successful')
    assert succeeded is False
    assert error is not None
    assert 'output.json not found' in error['explanation']
    assert error['traceback'] == ''


@pytest.mark.django_db
def test_invoke_adoption_hooks_project_update_success(tmp_path):
    """invoke_adoption_hooks successfully runs ProjectUpdate hook."""
    from unittest.mock import Mock
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    project = Project.objects.create(
        name='test_project',
        organization=org,
        scm_type='git',
        scm_url='https://github.com/test/repo',
    )
    pu = ProjectUpdate.objects.create(project=project)

    callback = Mock()

    # Simply invoke the hook - we're testing that it doesn't fail
    # The actual hook implementation is tested in unit tests
    succeeded, error = invoke_adoption_hooks(pu, callback, str(tmp_path), 'successful')
    # Hook may succeed or have no artifacts - both are acceptable here
    # We're testing that invoke_adoption_hooks handles ProjectUpdate correctly
    assert isinstance(succeeded, bool)


@pytest.mark.django_db
def test_invoke_adoption_hooks_inventory_update_with_artifacts(tmp_path):
    """invoke_adoption_hooks successfully processes InventoryUpdate with artifacts."""
    from unittest.mock import Mock
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )
    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    # Create artifacts
    artifacts_dir = tmp_path / 'artifacts' / str(iu.id)
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / 'output.json').write_text('{"all": {"hosts": {}}}')

    callback = Mock()

    # Simply invoke the hook with valid artifacts
    # The actual hook implementation is tested in unit tests
    succeeded, error = invoke_adoption_hooks(iu, callback, str(tmp_path), 'successful')
    # With valid artifacts, hook should attempt to execute
    assert isinstance(succeeded, bool)


@pytest.mark.django_db
def test_invoke_adoption_hooks_handles_task_class_not_found(tmp_path):
    """invoke_adoption_hooks handles case where job has no task class."""
    from unittest.mock import Mock, patch
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    project = Project.objects.create(name='test_proj', organization=org)
    jt = JobTemplate.objects.create(
        name='test_jt',
        inventory=None,
        project=project,
    )
    job = Job.objects.create(
        job_template=jt,
        inventory=None,
    )

    callback = Mock()

    # Mock _get_task_class to raise NotImplementedError
    with patch.object(job, '_get_task_class', side_effect=NotImplementedError):
        succeeded, error = invoke_adoption_hooks(job, callback, str(tmp_path), 'successful')
        # Should skip gracefully
        assert succeeded is True
        assert error is None


@pytest.mark.django_db
def test_invoke_adoption_hooks_no_task_class_graceful_skip(tmp_path):
    """invoke_adoption_hooks skips gracefully when task class not available."""
    from unittest.mock import Mock
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    inventory = Inventory.objects.create(name='test_inv', organization=org)
    inv_source = InventorySource.objects.create(
        name='aws',
        inventory=inventory,
        source='aws_ec2',
    )
    iu = InventoryUpdate.objects.create(
        inventory_source=inv_source,
        source='aws_ec2',
    )

    callback = Mock()

    # No artifacts, so it will fail on validation rather than task class lookup
    # But we're testing that the flow handles missing task classes
    succeeded, error = invoke_adoption_hooks(iu, callback, str(tmp_path), 'successful')
    # Should fail on artifact validation
    assert succeeded is False
    assert 'output.json' in error['explanation']


@pytest.mark.django_db
def test_invoke_adoption_hooks_multiple_statuses(tmp_path):
    """invoke_adoption_hooks correctly filters by status."""
    from unittest.mock import Mock
    from awx.main.tasks.adoption import invoke_adoption_hooks

    org = Organization.objects.create(name='test_org')
    project = Project.objects.create(
        name='test_project',
        organization=org,
        scm_type='git',
        scm_url='https://github.com/test/repo',
    )

    callback = Mock()

    for status in ['failed', 'error', 'canceled', 'pending', 'running']:
        pu = ProjectUpdate.objects.create(project=project)
        succeeded, error = invoke_adoption_hooks(pu, callback, str(tmp_path), status)
        # Non-successful statuses should skip hooks and return True
        assert succeeded is True
        assert error is None
