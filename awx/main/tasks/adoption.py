"""
Post-run hook invocation for adoption recovery.

When adoption reattaches to a work unit, some job types require post-execution
processing (e.g., InventoryUpdate must import discovered hosts). This module
provides invocation logic for type-specific hooks using the existing task
class hierarchy.
"""

import logging
import os
import time
import traceback

from awx.main.models.jobs import Job
from awx.main.models.projects import ProjectUpdate
from awx.main.models.inventory import InventoryUpdate

logger = logging.getLogger('awx.main.tasks.adoption')


def should_invoke_adoption_hook(job, status):
    """Determine if a job type should have its post-run hook invoked during adoption.

    Args:
        job: The UnifiedJob instance
        status: The job status ('successful', 'failed', etc.)

    Returns:
        bool: True if the hook should be called
    """
    # Only call hooks on successful completion
    if status != 'successful':
        return False

    # ProjectUpdate and InventoryUpdate always need hooks on success
    if isinstance(job, (ProjectUpdate, InventoryUpdate)):
        return True

    # Job hook only needed if job has inventory (for fact cache)
    if isinstance(job, Job):
        return bool(job.inventory_id)

    # Other job types don't need hooks
    return False


def _validate_adoption_artifacts(job, private_data_dir):
    """Validate that job artifacts exist and are readable before hook execution.

    Returns:
        (valid: bool, error_msg: str or None)
    """
    if not isinstance(job, InventoryUpdate):
        # ProjectUpdate, Job, and other types have no strict artifact requirements
        return True, None

    # InventoryUpdate hook needs output.json with discovered inventory
    output_json = os.path.join(private_data_dir, 'artifacts', str(job.id), 'output.json')
    if not os.path.exists(output_json):
        return False, f'InventoryUpdate {job.id}: output.json not found at {output_json}'
    if not os.access(output_json, os.R_OK):
        return False, f'InventoryUpdate {job.id}: output.json not readable at {output_json}'
    return True, None


def _get_task_class_for_hook(job):
    """Get task class for job, returning None if unavailable or lacks post_run_hook."""
    try:
        task_class = job._get_task_class()
    except (NotImplementedError, AttributeError):
        logger.debug(f'Job {job.id}: no task class available, skipping adoption hooks')
        return None

    if not task_class or not hasattr(task_class, 'post_run_hook'):
        logger.debug(f'Job {job.id}: task class {task_class} has no post_run_hook, skipping')
        return None

    return task_class


def _build_hook_error_info(exc, hook_start_time):
    """Build error info dict from exception, handling PostRunError specially."""
    elapsed = time.time() - hook_start_time
    exc_type = type(exc).__name__

    if exc_type == 'PostRunError':
        logger.warning(f'Adoption hook raised PostRunError after {elapsed:.2f}s: {exc.args[0] if exc.args else str(exc)}')
        return {
            'explanation': exc.args[0] if exc.args else str(exc),
            'traceback': getattr(exc, 'tb', '') or '',
            'status_override': getattr(exc, 'status', 'failed'),
        }

    logger.exception(f'Adoption hook raised unexpected exception after {elapsed:.2f}s')
    return {
        'explanation': f'Adoption hook failed: {exc_type}: {str(exc)}',
        'traceback': traceback.format_exc(),
    }


def _override_job_env(job, private_data_dir):
    """Temporarily override job's AWX_PRIVATE_DATA_DIR for hook execution.

    Returns (original_env_copy, restore_fn) where restore_fn() restores original.
    """
    job.refresh_from_db(fields=['job_env'])
    original_env = dict(job.job_env or {})

    if job.job_env is None:
        job.job_env = {}
    job.job_env['AWX_PRIVATE_DATA_DIR'] = private_data_dir

    return original_env


def invoke_adoption_hooks(job, callback, private_data_dir, status):
    """Call post-run hook for a job during adoption, if applicable.

    Hooks run AFTER job execution completes, so no separate timeout is imposed.
    The job's own runtime already bounded execution time. The hook just finalizes
    results (e.g., imports inventory, caches project files). If adoption task
    itself is killed (system shutdown), the finally block cleans up artifacts.

    Args:
        job: The UnifiedJob being adopted
        callback: The RunnerCallback from adoption stream
        private_data_dir: The adoption's private_data_dir (not lost controller's)
        status: The job status ('successful', 'failed', etc.)

    Returns:
        (hook_succeeded: bool, error_info: dict or None)

    If hook_succeeded is False, caller should mark job as failed.
    error_info contains 'explanation' and 'traceback' for logging.
    """
    if not should_invoke_adoption_hook(job, status):
        return True, None

    # Validate artifacts before attempting hook
    artifacts_valid, validation_error = _validate_adoption_artifacts(job, private_data_dir)
    if not artifacts_valid:
        logger.warning(f'Job {job.id}: artifact validation failed before hook: {validation_error}')
        return False, {
            'explanation': validation_error,
            'traceback': '',
        }

    # Get the task class for this job type
    task_class = _get_task_class_for_hook(job)
    if not task_class:
        return True, None

    logger.info(f'Job {job.id} (type={job.__class__.__name__}): invoking {task_class.__name__}.post_run_hook() during adoption (status={status})')

    hook_start_time = time.time()
    try:
        task_instance = task_class()
        task_instance.instance = job
        task_instance.runner_callback = callback
        task_instance.private_data_dir = private_data_dir

        original_env = _override_job_env(job, private_data_dir)
        try:
            task_instance.post_run_hook(job, status)
            elapsed = time.time() - hook_start_time
            logger.info(f'Job {job.id}: adoption hook succeeded in {elapsed:.2f}s')
            return True, None
        finally:
            job.job_env = original_env

    except Exception as exc:
        error_info = _build_hook_error_info(exc, hook_start_time)
        return False, error_info
