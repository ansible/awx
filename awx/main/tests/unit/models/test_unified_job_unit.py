import pytest
import mock

from awx.main.models import (
    UnifiedJob,
    WorkflowJob,
    WorkflowJobNode,
    Job
)


def test_unified_job_workflow_attributes():
    with mock.patch('django.db.ConnectionRouter.db_for_write'):
        job = UnifiedJob(id=1, name="job-1", launch_type="workflow")
        job.unified_job_node = WorkflowJobNode(workflow_job=WorkflowJob(pk=1))

        assert job.spawned_by_workflow is True
        assert job.workflow_job_id == 1


@pytest.fixture
def unified_job(mocker):
    mocker.patch.object(UnifiedJob, 'can_cancel', return_value=True)
    j = UnifiedJob()
    j.status = 'pending'
    j.cancel_flag = None
    j.save = mocker.MagicMock()
    j.websocket_emit_status = mocker.MagicMock()
    return j


def test_cancel(unified_job):

    unified_job.cancel()

    assert unified_job.cancel_flag is True
    assert unified_job.status == 'canceled'
    assert unified_job.job_explanation == ''
    # Note: the websocket emit status check is just reflecting the state of the current code.
    # Some more thought may want to go into only emitting canceled if/when the job record
    # status is changed to canceled. Unlike, currently, where it's emitted unconditionally.
    unified_job.websocket_emit_status.assert_called_with("canceled")
    unified_job.save.assert_called_with(update_fields=['cancel_flag', 'status'])


def test_cancel_job_explanation(unified_job):
    job_explanation = 'giggity giggity'

    unified_job.cancel(job_explanation=job_explanation)

    assert unified_job.job_explanation == job_explanation
    unified_job.save.assert_called_with(update_fields=['cancel_flag', 'status', 'job_explanation'])


def test_log_representation():
    '''
    Common representation used inside of log messages
    '''
    uj = UnifiedJob(status='running', id=4)
    job = Job(status='running', id=4)
    assert job.log_format == 'job 4 (running)'
    assert uj.log_format == 'unified_job 4 (running)'

