from unittest import mock

import pytest
from rest_framework.exceptions import ValidationError

from awx.api.serializers import (
    ActivityStreamSerializer,
    AdHocCommandRelaunchSerializer,
    AnsibleFactsSerializer,
    GroupTreeSerializer,
    HostSerializer,
    JobCreateScheduleSerializer,
    JobHostSummarySerializer,
    JobRelaunchSerializer,
    NotificationSerializer,
    OpaQueryPathMixin,
    ProjectUpdateEventSerializer,
    UnifiedJobSerializer,
    UnifiedJobStdoutSerializer,
    WorkflowApprovalSerializer,
    WorkflowJobLaunchSerializer,
    reverse_gfk,
)
from awx.main.constants import ACTIVE_STATES
from awx.main.models import JobLaunchConfig, WorkflowApproval, WorkflowJobTemplate


def _mock(**kwargs):
    """Build a Mock with a real `.name` attribute.

    unittest.mock.Mock(name=...) only sets the mock's repr name, so
    getattr(obj, 'name') would return another Mock instead of the string.
    """
    name = kwargs.pop('name', None)
    obj = mock.Mock(**kwargs)
    if name is not None:
        obj.name = name
    return obj


def test_reverse_gfk_empty_when_object_missing():
    assert reverse_gfk(None, None) == {}
    assert reverse_gfk(object(), None) == {}


def test_reverse_gfk_uses_absolute_url():
    class Organization:
        def get_absolute_url(self, request=None):
            return '/api/v2/organizations/1/'

    assert reverse_gfk(Organization(), None) == {'organization': '/api/v2/organizations/1/'}


def test_opa_query_path_rejects_unencoded_url():
    with pytest.raises(ValidationError):
        OpaQueryPathMixin().validate_opa_query_path('not a valid path')


def test_unified_job_stdout_types():
    assert UnifiedJobStdoutSerializer().get_types() == [
        'project_update',
        'inventory_update',
        'job',
        'ad_hoc_command',
        'system_job',
    ]


def test_unified_job_launched_by():
    serializer = UnifiedJobSerializer()
    assert serializer.get_launched_by(None) is None
    obj = mock.Mock(launched_by={'id': 7})
    assert serializer.get_launched_by(obj) == {'id': 7}


def test_unified_job_sub_serializer_workflow_approval():
    obj = mock.MagicMock(spec=WorkflowApproval)
    assert UnifiedJobSerializer().get_sub_serializer(obj) is WorkflowApprovalSerializer


def test_ansible_facts_to_representation():
    obj = mock.Mock(ansible_facts={'os': 'rhel'})
    assert AnsibleFactsSerializer().to_representation(obj) == {'os': 'rhel'}


def test_group_tree_children_none():
    assert GroupTreeSerializer().get_children(None) == {}


def test_adhoc_relaunch_to_representation():
    serializer = AdHocCommandRelaunchSerializer()
    assert serializer.to_representation(None) == {}
    obj = mock.Mock(passwords_needed_to_start=['ssh_password'])
    assert serializer.to_representation(obj) == {'ssh_password': ''}


class TestHostToRepresentation:
    def test_related_includes_last_job_links(self):
        serializer = HostSerializer()
        serializer.reverse = mock.Mock(return_value='/x/')
        obj = mock.Mock(pk=1, instance_id=9)
        obj.inventory.kind = 'constructed'
        obj.inventory.pk = 2
        obj.latest_summary = mock.Mock(pk=3, job_id=4)
        with mock.patch('awx.api.serializers.BaseSerializer.get_related', return_value={}):
            related = serializer.get_related(obj)
        assert 'last_job_host_summary' in related
        assert 'last_job' in related

    def test_empty_obj_returns_parent_payload(self):
        serializer = HostSerializer()
        with mock.patch('awx.api.serializers.BaseSerializer.to_representation', return_value={'inventory': 1}):
            assert serializer.to_representation(None) == {'inventory': 1}

    def test_nulls_missing_inventory(self):
        serializer = HostSerializer()
        obj = mock.Mock(inventory=None)
        with mock.patch('awx.api.serializers.BaseSerializer.to_representation', return_value={'inventory': 9}):
            assert serializer.to_representation(obj)['inventory'] is None


@pytest.mark.django_db
class TestJobRelaunchSerializerPaths:
    def test_missing_credential_passwords(self):
        serializer = JobRelaunchSerializer()
        serializer.instance = mock.Mock(passwords_needed_to_start=['ssh_password', 'become_password'])
        with pytest.raises(ValidationError):
            serializer.validate_credential_passwords({'ssh_password': ''})

    def test_to_representation_injects_password_keys(self):
        view = mock.Mock(_raw_data_form_marker=True)
        serializer = JobRelaunchSerializer(context={'view': view})
        obj = mock.Mock(passwords_needed_to_start=['ssh_password'])
        with mock.patch('awx.api.serializers.BaseSerializer.to_representation', return_value={}):
            assert serializer.to_representation(obj)['ssh_password'] == ''

    def test_passwords_needed_to_start(self):
        serializer = JobRelaunchSerializer()
        assert serializer.get_passwords_needed_to_start(None) == ''
        obj = mock.Mock(passwords_needed_to_start=['ssh_password'])
        assert serializer.get_passwords_needed_to_start(obj) == ['ssh_password']

    def test_retry_counts_while_running(self):
        serializer = JobRelaunchSerializer()
        obj = mock.Mock(status=next(iter(ACTIVE_STATES)))
        assert 'not available' in str(serializer.get_retry_counts(obj))

    def test_retry_counts_when_finished(self):
        serializer = JobRelaunchSerializer()
        obj = mock.Mock(status='successful')
        obj.retry_qs.return_value.count.return_value = 2
        counts = serializer.get_retry_counts(obj)
        assert counts['all'] == 2
        assert counts['failed'] == 2

    def test_validate_missing_project(self):
        serializer = JobRelaunchSerializer()
        serializer.instance = mock.Mock(project=None, inventory=mock.Mock(pending_deletion=False))
        with pytest.raises(ValidationError):
            serializer.validate({})

    def test_validate_missing_inventory(self):
        serializer = JobRelaunchSerializer()
        serializer.instance = mock.Mock(project=mock.Mock(), inventory=None)
        with pytest.raises(ValidationError):
            serializer.validate({})

    def test_validate_inventory_pending_deletion(self):
        serializer = JobRelaunchSerializer()
        serializer.instance = mock.Mock(project=mock.Mock(), inventory=mock.Mock(pending_deletion=True))
        with pytest.raises(ValidationError):
            serializer.validate({})


class TestJobCreateScheduleSerializerPaths:
    def test_can_schedule(self):
        obj = mock.Mock(can_schedule=True)
        assert JobCreateScheduleSerializer().get_can_schedule(obj) is True

    def test_summarize_copies_fk_fields(self):
        obj = _mock(id=3, name='inv', description='d')
        summary = JobCreateScheduleSerializer._summarize('host', obj)
        assert summary['id'] == 3
        assert summary['name'] == 'inv'

    def test_get_prompts_summarizes_related_objects(self):
        inventory = _mock(id=1, name='inv', description='', has_active_failures=False)
        ee = _mock(id=2, name='ee', description='', image='img')
        cred = _mock(id=3, name='cred', description='', kind='ssh', cloud=False, kubernetes=False, credential_type_id=1)
        ig = _mock(id=4, name='ig', is_container_group=False)
        config = mock.Mock()
        config.prompts_dict.return_value = {
            'inventory': inventory,
            'execution_environment': ee,
            'credentials': [cred],
            'instance_groups': [ig],
            'labels': True,
        }
        job = mock.Mock(launch_config=config)
        serializer = JobCreateScheduleSerializer()
        serializer._summary_field_labels = mock.Mock(return_value=[{'id': 9, 'name': 'l'}])
        prompts = serializer.get_prompts(job)
        assert prompts['inventory']['id'] == 1
        assert prompts['execution_environment']['id'] == 2
        assert prompts['credentials'][0]['id'] == 3
        assert prompts['instance_groups'][0]['id'] == 4
        assert prompts['labels'] == [{'id': 9, 'name': 'l'}]

    def test_get_prompts_without_launch_config(self):
        class JobWithoutConfig:
            @property
            def launch_config(self):
                raise JobLaunchConfig.DoesNotExist()

        prompts = JobCreateScheduleSerializer().get_prompts(JobWithoutConfig())
        assert 'all' in prompts


class TestNotificationSerializerBody:
    def test_webhook_dict_body(self):
        obj = mock.Mock(notification_type='webhook', body={'body': 'hello'})
        assert NotificationSerializer().get_body(obj) == 'hello'

    def test_webhook_json_string_body(self):
        obj = mock.Mock(notification_type='pagerduty', body='{"ok": true}')
        assert NotificationSerializer().get_body(obj) == {'ok': True}

    def test_webhook_invalid_json_string_body(self):
        obj = mock.Mock(notification_type='awssns', body='not-json')
        assert NotificationSerializer().get_body(obj) == 'not-json'

    def test_plain_body_passthrough(self):
        obj = mock.Mock(notification_type='email', body='text')
        assert NotificationSerializer().get_body(obj) == 'text'


class TestJobHostSummarySerializerPaths:
    def test_get_related_includes_host(self):
        serializer = JobHostSummarySerializer()
        serializer.reverse = mock.Mock(side_effect=lambda *a, **k: '/x/')
        obj = mock.Mock(job=mock.Mock(pk=1), host=mock.Mock(pk=2))
        with mock.patch('awx.api.serializers.BaseSerializer.get_related', return_value={}):
            related = serializer.get_related(obj)
        assert 'job' in related
        assert 'host' in related

    def test_summary_fields_adds_job_template(self):
        serializer = JobHostSummarySerializer()
        obj = mock.Mock()
        obj.job.job_template.id = 11
        obj.job.job_template.name = 'jt'
        with mock.patch('awx.api.serializers.BaseSerializer.get_summary_fields', return_value={'job': {}}):
            summary = serializer.get_summary_fields(obj)
        assert summary['job']['job_template_id'] == 11
        assert summary['job']['job_template_name'] == 'jt'

    def test_summary_fields_tolerates_missing_job(self):
        serializer = JobHostSummarySerializer()
        obj = mock.Mock()
        with mock.patch('awx.api.serializers.BaseSerializer.get_summary_fields', return_value={}):
            assert serializer.get_summary_fields(obj) == {}


class TestWorkflowJobLaunchSerializerPaths:
    def test_survey_enabled(self):
        serializer = WorkflowJobLaunchSerializer()
        assert serializer.get_survey_enabled(None) is False
        obj = mock.Mock(survey_enabled=True, survey_spec={'spec': []})
        assert serializer.get_survey_enabled(obj) is True

    def test_workflow_job_template_data(self):
        obj = _mock(name='wf', id=5, description='d')
        assert WorkflowJobLaunchSerializer().get_workflow_job_template_data(obj) == {'name': 'wf', 'id': 5, 'description': 'd'}

    def test_defaults_inventory_and_labels(self):
        mapping = {'inventory': None, 'labels': None, 'limit': None}
        obj = mock.Mock()
        obj.inventory.name = 'inv'
        obj.inventory.pk = 8
        obj.limit = 'webservers'
        label = _mock(id=1, name='prod')
        obj.labels.all.return_value = [label]
        with mock.patch.object(WorkflowJobTemplate, 'get_ask_mapping', return_value=mapping):
            defaults = WorkflowJobLaunchSerializer().get_defaults(obj)
        assert defaults['inventory'] == {'name': 'inv', 'id': 8}
        assert defaults['labels'] == [{'id': 1, 'name': 'prod'}]
        assert defaults['limit'] == 'webservers'


class TestActivityStreamSerializerPaths:
    def test_get_changes(self):
        serializer = ActivityStreamSerializer()
        assert serializer.get_changes(None) == {}
        assert serializer.get_changes(mock.Mock(changes='{"a": 1}')) == {'a': 1}
        assert serializer.get_changes(mock.Mock(changes='not-json')) == {}

    def test_object_association(self):
        serializer = ActivityStreamSerializer()
        assert serializer.get_object_association(mock.Mock(object_relationship_type='')) == ''
        assert serializer.get_object_association(mock.Mock(object_relationship_type='awx.main.models.inventory.Inventory.admin_role')) == 'role'
        rel = 'awx.main.models.organization.Organization_notification_templates_success'
        assert 'notification' in serializer.get_object_association(mock.Mock(object_relationship_type=rel))

    def test_object_type_role(self):
        serializer = ActivityStreamSerializer()
        assert serializer.get_object_type(mock.Mock(object_relationship_type='')) == ''
        rel = 'awx.main.models.inventory.Inventory.admin_role'
        assert serializer.get_object_type(mock.Mock(object_relationship_type=rel)) == 'inventory'


class TestProjectUpdateEventSanitization:
    def test_sanitizes_git_event_data(self):
        serializer = ProjectUpdateEventSerializer()
        obj = mock.Mock(event_data={'task_action': 'git', 'msg': 'ok'})
        assert serializer.get_event_data(obj)['task_action'] == 'git'

    def test_returns_empty_on_sanitize_failure(self):
        serializer = ProjectUpdateEventSerializer()
        obj = mock.Mock(event_data={'task_action': 'svn'})
        with mock.patch('awx.api.serializers.json.dumps', side_effect=ValueError('boom')):
            assert serializer.get_event_data(obj) == {}

    def test_passthrough_for_other_actions(self):
        serializer = ProjectUpdateEventSerializer()
        obj = mock.Mock(event_data={'task_action': 'debug', 'msg': 'hi'})
        assert serializer.get_event_data(obj) == obj.event_data


class TestUnifiedJobSummaryFields:
    def test_spawned_by_workflow_copies_job_summary(self):
        serializer = UnifiedJobSerializer()
        workflow_job = _mock(id=10, name='wf', description='', status='successful', failed=False, elapsed=1.5, type='workflow_job', canceled_on=None)
        obj = mock.Mock(spawned_by_workflow=True, ancestor_job=None)
        obj.unified_job_node.workflow_job = workflow_job
        with mock.patch('awx.api.serializers.BaseSerializer.get_summary_fields', return_value={}):
            summary = serializer.get_summary_fields(obj)
        assert summary['source_workflow_job']['id'] == 10
        assert summary['source_workflow_job']['name'] == 'wf'


def test_unified_job_elapsed_for_running_job():
    serializer = UnifiedJobSerializer()
    started = mock.Mock()
    td = mock.Mock(microseconds=0, seconds=5, days=0)
    obj = mock.Mock(pk=1, started=started, finished=None, job_explanation='')
    with mock.patch.object(UnifiedJobSerializer, 'get_sub_serializer', return_value=None):
        with mock.patch('awx.api.serializers.BaseSerializer.to_representation', return_value={'elapsed': 0, 'job_explanation': ''}):
            with mock.patch('awx.api.serializers.now', return_value=mock.Mock(__sub__=lambda self, other: td)):
                ret = serializer.to_representation(obj)
    assert ret['elapsed'] == 5.0
