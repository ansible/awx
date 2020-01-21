import pytest
from unittest import mock

from awx.main.models import (
    UnifiedJob,
    UnifiedJobTemplate,
    WorkflowJob,
    WorkflowJobNode,
    WorkflowApprovalTemplate,
    Job,
    User,
    Project,
    JobTemplate,
    Inventory
)


def test_incorrectly_formatted_variables():
    bad_data = '{"bar":"foo'
    accepted, ignored, errors = UnifiedJobTemplate().accept_or_ignore_variables(bad_data)
    assert not accepted
    assert ignored == bad_data
    assert 'Cannot parse as JSON' in str(errors['extra_vars'][0])


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
    unified_job.save.assert_called_with(update_fields=['cancel_flag', 'start_args', 'status'])


def test_cancel_job_explanation(unified_job):
    job_explanation = 'giggity giggity'

    unified_job.cancel(job_explanation=job_explanation)

    assert unified_job.job_explanation == job_explanation
    unified_job.save.assert_called_with(update_fields=['cancel_flag', 'start_args', 'status', 'job_explanation'])


def test_organization_copy_to_jobs():
    '''
    All unified job types should infer their organization from their template organization
    '''
    for cls in UnifiedJobTemplate.__subclasses__():
        if cls is WorkflowApprovalTemplate:
            continue  # these do not track organization
        assert 'organization' in cls._get_unified_job_field_names(), cls


def test_log_representation():
    '''
    Common representation used inside of log messages
    '''
    uj = UnifiedJob(status='running', id=4)
    job = Job(status='running', id=4)
    assert job.log_format == 'job 4 (running)'
    assert uj.log_format == 'unified_job 4 (running)'


class TestMetaVars:
    '''
    Corresponding functional test exists for cases with indirect relationships
    '''

    def test_job_metavars(self):
        maker = User(username='joe', pk=47, id=47)
        inv = Inventory(name='example-inv', id=45)
        assert Job(
            name='fake-job',
            pk=42, id=42,
            launch_type='manual',
            created_by=maker,
            inventory=inv
        ).awx_meta_vars() == {
            'tower_job_id': 42,
            'awx_job_id': 42,
            'tower_job_launch_type': 'manual',
            'awx_job_launch_type': 'manual',
            'awx_user_name': 'joe',
            'tower_user_name': 'joe',
            'awx_user_email': '',
            'tower_user_email': '',
            'awx_user_first_name': '',
            'tower_user_first_name': '',
            'awx_user_last_name': '',
            'tower_user_last_name': '',
            'awx_user_id': 47,
            'tower_user_id': 47,
            'tower_inventory_id': 45,
            'awx_inventory_id': 45,
            'tower_inventory_name': 'example-inv',
            'awx_inventory_name': 'example-inv'
        }

    def test_project_update_metavars(self):
        data = Job(
            name='fake-job',
            pk=40, id=40,
            launch_type='manual',
            project=Project(
                name='jobs-sync',
                scm_revision='12345444'
            ),
            job_template=JobTemplate(
                name='jobs-jt',
                id=92, pk=92
            )
        ).awx_meta_vars()
        assert data['awx_project_revision'] == '12345444'
        assert 'tower_job_template_id' in data
        assert data['tower_job_template_id'] == 92
        assert data['tower_job_template_name'] == 'jobs-jt'
