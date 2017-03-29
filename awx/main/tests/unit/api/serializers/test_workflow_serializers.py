# Python
import pytest
import mock

# AWX
from awx.api.serializers import (
    WorkflowJobTemplateSerializer,
    WorkflowNodeBaseSerializer,
    WorkflowJobTemplateNodeSerializer,
    WorkflowJobNodeSerializer,
)
from awx.main.models import (
    Job,
    WorkflowJobTemplateNode,
    WorkflowJob,
    WorkflowJobNode,
)


@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x,y: {})
class TestWorkflowJobTemplateSerializerGetRelated():
    @pytest.fixture
    def workflow_job_template(self, workflow_job_template_factory):
        wfjt = workflow_job_template_factory('hello world', persisted=False).workflow_job_template
        wfjt.pk = 3
        return wfjt

    @pytest.mark.parametrize("related_resource_name", [
        'workflow_jobs',
        'launch',
        'workflow_nodes',
    ])
    def test_get_related(self, mocker, test_get_related, workflow_job_template, related_resource_name):
        test_get_related(WorkflowJobTemplateSerializer,
                         workflow_job_template,
                         'workflow_job_templates',
                         related_resource_name)


@mock.patch('awx.api.serializers.BaseSerializer.get_related', lambda x,y: {})
class TestWorkflowNodeBaseSerializerGetRelated():
    @pytest.fixture
    def job_template(self, job_template_factory):
        jt = job_template_factory(name="blah", persisted=False).job_template
        jt.pk = 1
        return jt

    @pytest.fixture
    def workflow_job_template_node_related(self, job_template):
        return WorkflowJobTemplateNode(pk=1, unified_job_template=job_template)

    @pytest.fixture
    def workflow_job_template_node(self):
        return WorkflowJobTemplateNode(pk=1)

    def test_workflow_unified_job_template_present(self, get_related_mock_and_run, workflow_job_template_node_related):
        related = get_related_mock_and_run(WorkflowNodeBaseSerializer, workflow_job_template_node_related)
        assert 'unified_job_template' in related
        assert related['unified_job_template'] == '/api/v2/%s/%d/' % ('job_templates', workflow_job_template_node_related.unified_job_template.pk)

    def test_workflow_unified_job_template_absent(self, workflow_job_template_node):
        related = WorkflowJobTemplateNodeSerializer().get_related(workflow_job_template_node)
        assert 'unified_job_template' not in related


@mock.patch('awx.api.serializers.WorkflowNodeBaseSerializer.get_related', lambda x,y: {})
class TestWorkflowJobTemplateNodeSerializerGetRelated():
    @pytest.fixture
    def workflow_job_template_node(self):
        return WorkflowJobTemplateNode(pk=1)

    @pytest.fixture
    def workflow_job_template(self, workflow_job_template_factory):
        wfjt = workflow_job_template_factory("bliggity", persisted=False).workflow_job_template
        wfjt.pk = 1
        return wfjt

    @pytest.fixture
    def job_template(self, job_template_factory):
        jt = job_template_factory(name="blah", persisted=False).job_template
        jt.pk = 1
        return jt

    @pytest.fixture
    def workflow_job_template_node_related(self, workflow_job_template_node, workflow_job_template):
        workflow_job_template_node.workflow_job_template = workflow_job_template
        return workflow_job_template_node

    @pytest.mark.parametrize("related_resource_name", [
        'success_nodes',
        'failure_nodes',
        'always_nodes',
    ])
    def test_get_related(self, test_get_related, workflow_job_template_node, related_resource_name):
        test_get_related(WorkflowJobTemplateNodeSerializer,
                         workflow_job_template_node,
                         'workflow_job_template_nodes',
                         related_resource_name)

    def test_workflow_job_template_present(self, get_related_mock_and_run, workflow_job_template_node_related):
        related = get_related_mock_and_run(WorkflowJobTemplateNodeSerializer, workflow_job_template_node_related)
        assert 'workflow_job_template' in related
        assert related['workflow_job_template'] == '/api/v2/%s/%d/' % ('workflow_job_templates', workflow_job_template_node_related.workflow_job_template.pk)

    def test_workflow_job_template_absent(self, workflow_job_template_node):
        related = WorkflowJobTemplateNodeSerializer().get_related(workflow_job_template_node)
        assert 'workflow_job_template' not in related


class FakeView:
    def __init__(self, obj):
        self.obj = obj

    def get_object(self):
        return self.obj


class FakeRequest:
    pass


class TestWorkflowJobTemplateNodeSerializerCharPrompts():
    @pytest.fixture
    def WFJT_serializer(self):
        serializer = WorkflowJobTemplateNodeSerializer()
        node = WorkflowJobTemplateNode(pk=1)
        node.char_prompts = {'limit': 'webservers'}
        serializer.instance = node
        view = FakeView(node)
        view.request = FakeRequest()
        view.request.method = "PATCH"
        serializer.context = {'view': view}
        return serializer

    def test_change_single_field(self, WFJT_serializer):
        "Test that a single prompt field can be changed without affecting other fields"
        internal_value = WFJT_serializer.to_internal_value({'job_type': 'check'})
        assert internal_value['char_prompts']['job_type'] == 'check'
        assert internal_value['char_prompts']['limit'] == 'webservers'

    def test_null_single_field(self, WFJT_serializer):
        "Test that a single prompt field can be removed without affecting other fields"
        internal_value = WFJT_serializer.to_internal_value({'job_type': None})
        assert 'job_type' not in internal_value['char_prompts']
        assert internal_value['char_prompts']['limit'] == 'webservers'


@mock.patch('awx.api.serializers.WorkflowNodeBaseSerializer.get_related', lambda x,y: {})
class TestWorkflowJobNodeSerializerGetRelated():
    @pytest.fixture
    def workflow_job_node(self):
        return WorkflowJobNode(pk=1)

    @pytest.fixture
    def workflow_job(self):
        return WorkflowJob(pk=1)

    @pytest.fixture
    def job(self):
        return Job(name="blah", pk=1)

    @pytest.fixture
    def workflow_job_node_related(self, workflow_job_node, workflow_job, job):
        workflow_job_node.workflow_job = workflow_job
        workflow_job_node.job = job
        return workflow_job_node

    @pytest.mark.parametrize("related_resource_name", [
        'success_nodes',
        'failure_nodes',
        'always_nodes',
    ])
    def test_get_related(self, test_get_related, workflow_job_node, related_resource_name):
        test_get_related(WorkflowJobNodeSerializer,
                         workflow_job_node,
                         'workflow_job_nodes',
                         related_resource_name)

    def test_workflow_job_present(self, get_related_mock_and_run, workflow_job_node_related):
        related = get_related_mock_and_run(WorkflowJobNodeSerializer, workflow_job_node_related)
        assert 'workflow_job' in related
        assert related['workflow_job'] == '/api/v2/%s/%d/' % ('workflow_jobs', workflow_job_node_related.workflow_job.pk)

    def test_workflow_job_absent(self, workflow_job_node):
        related = WorkflowJobNodeSerializer().get_related(workflow_job_node)
        assert 'workflow_job' not in related

    def test_job_present(self, get_related_mock_and_run, workflow_job_node_related):
        related = get_related_mock_and_run(WorkflowJobNodeSerializer, workflow_job_node_related)
        assert 'job' in related
        assert related['job'] == '/api/v2/%s/%d/' % ('jobs', workflow_job_node_related.job.pk)

    def test_job_absent(self, workflow_job_node):
        related = WorkflowJobNodeSerializer().get_related(workflow_job_node)
        assert 'job' not in related
