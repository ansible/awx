from unittest import mock

from awx.main.models import UnifiedJob, UnifiedJobTemplate, WorkflowJob, WorkflowJobNode, WorkflowApprovalTemplate, Job, User, Project, JobTemplate, Inventory
from awx.main.utils.common import get_job_variable_prefixes


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


def test_ancestor_job_returns_self_when_not_workflow():
    job = UnifiedJob(id=1, name="job-1", launch_type="manual")
    assert job.ancestor_job is job


def test_ancestor_job_returns_self_when_workflow_job_deleted():
    """Regression test for https://github.com/ansible/awx/issues/16250

    When a workflow job is deleted while its child jobs still exist,
    get_workflow_job() returns None. ancestor_job must not crash.
    """
    job = UnifiedJob(id=1, name="job-1", launch_type="workflow")
    with mock.patch.object(UnifiedJob, 'get_workflow_job', return_value=None):
        assert job.ancestor_job is job


def test_ancestor_job_traverses_workflow():
    with mock.patch('django.db.ConnectionRouter.db_for_write'):
        wj = WorkflowJob(pk=1, launch_type="manual")
        child = UnifiedJob(id=2, name="child", launch_type="workflow")
        child.unified_job_node = WorkflowJobNode(workflow_job=wj)

        assert child.ancestor_job is wj


def test_organization_copy_to_jobs():
    """
    All unified job types should infer their organization from their template organization
    """
    for cls in UnifiedJobTemplate.__subclasses__():
        if cls is WorkflowApprovalTemplate:
            continue  # these do not track organization
        assert 'organization' in cls._get_unified_job_field_names(), cls


def test_log_representation():
    """
    Common representation used inside of log messages
    """
    uj = UnifiedJob(status='running', id=4)
    job = Job(status='running', id=4)
    assert job.log_format == 'job 4 (running)'
    assert uj.log_format == 'unified_job 4 (running)'


class TestMetaVars:
    """
    Corresponding functional test exists for cases with indirect relationships
    """

    def test_job_metavars(self):
        maker = User(username='joe', pk=47, id=47)
        inv = Inventory(name='example-inv', id=45)
        result_hash = {}
        for name in get_job_variable_prefixes():
            result_hash['{}_job_id'.format(name)] = 42
            result_hash['{}_job_launch_type'.format(name)] = 'manual'
            result_hash['{}_user_name'.format(name)] = 'joe'
            result_hash['{}_user_email'.format(name)] = ''
            result_hash['{}_user_first_name'.format(name)] = ''
            result_hash['{}_user_last_name'.format(name)] = ''
            result_hash['{}_user_id'.format(name)] = 47
            result_hash['{}_inventory_id'.format(name)] = 45
            result_hash['{}_inventory_name'.format(name)] = 'example-inv'
            result_hash['{}_execution_node'.format(name)] = 'example-exec-node'
        assert (
            Job(name='fake-job', pk=42, id=42, launch_type='manual', created_by=maker, inventory=inv, execution_node='example-exec-node').awx_meta_vars()
            == result_hash
        )

    def test_project_update_metavars(self):
        data = Job(
            name='fake-job',
            pk=40,
            id=40,
            launch_type='manual',
            project=Project(name='jobs-sync', scm_revision='12345444'),
            job_template=JobTemplate(name='jobs-jt', id=92, pk=92),
        ).awx_meta_vars()
        for name in get_job_variable_prefixes():
            assert data['{}_project_revision'.format(name)] == '12345444'
            assert '{}_job_template_id'.format(name) in data
            assert data['{}_job_template_id'.format(name)] == 92
            assert data['{}_job_template_name'.format(name)] == 'jobs-jt'


class TestGetJobVariablePrefixes:
    """Tests for the get_job_variable_prefixes() helper function."""

    def test_default_returns_both(self):
        from django.conf import settings

        with mock.patch.object(settings, 'INCLUDE_DEPRECATED_AWX_VAR_PREFIX', True, create=True):
            assert get_job_variable_prefixes() == ['awx', 'tower']

    def test_disabled_returns_tower_only(self):
        from django.conf import settings

        with mock.patch.object(settings, 'INCLUDE_DEPRECATED_AWX_VAR_PREFIX', False, create=True):
            assert get_job_variable_prefixes() == ['tower']

    def test_fallback_when_setting_not_available(self):
        """When setting is not available, falls back to both prefixes for backward compatibility."""
        fake_settings = mock.MagicMock(spec=[])
        with mock.patch('django.conf.settings', fake_settings):
            assert get_job_variable_prefixes() == ['awx', 'tower']

    def test_job_metavars_both_prefixes(self):
        """With INCLUDE_DEPRECATED_AWX_VAR_PREFIX=True, both awx_ and tower_ variables."""
        from django.conf import settings

        with mock.patch.object(settings, 'INCLUDE_DEPRECATED_AWX_VAR_PREFIX', True, create=True):
            data = Job(name='fake-job', pk=1, id=1, launch_type='manual').awx_meta_vars()
            assert 'awx_job_id' in data
            assert 'tower_job_id' in data

    def test_job_metavars_tower_only(self):
        """With INCLUDE_DEPRECATED_AWX_VAR_PREFIX=False, only tower_ prefixed variables."""
        from django.conf import settings

        with mock.patch.object(settings, 'INCLUDE_DEPRECATED_AWX_VAR_PREFIX', False, create=True):
            data = Job(name='fake-job', pk=1, id=1, launch_type='manual').awx_meta_vars()
            assert 'tower_job_id' in data
            assert 'awx_job_id' not in data
