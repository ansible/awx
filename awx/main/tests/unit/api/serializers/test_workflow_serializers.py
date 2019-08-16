# Python
import pytest
from unittest import mock

# AWX
from awx.api.serializers import (
    WorkflowJobTemplateSerializer,
    WorkflowJobTemplateNodeSerializer,
    WorkflowJobNodeSerializer,
)
from awx.main.models import (
    Job,
    WorkflowJobTemplateNode,
    WorkflowJob,
    WorkflowJobNode,
    WorkflowJobTemplate,
    Project,
    Inventory,
    JobTemplate
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
        'webhook_key',
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
        related = get_related_mock_and_run(WorkflowJobTemplateNodeSerializer, workflow_job_template_node_related)
        assert 'unified_job_template' in related
        assert related['unified_job_template'] == '/api/v2/%s/%d/' % ('job_templates', workflow_job_template_node_related.unified_job_template.pk)

    def test_workflow_unified_job_template_absent(self, workflow_job_template_node):
        related = WorkflowJobTemplateNodeSerializer().get_related(workflow_job_template_node)
        assert 'unified_job_template' not in related


@mock.patch('awx.api.serializers.BaseSerializer.get_related', lambda x,y: {})
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

        view = FakeView(node)
        view.request = FakeRequest()
        view.request.method = "PATCH"

        serializer = WorkflowJobTemplateNodeSerializer()
        serializer = WorkflowJobTemplateNodeSerializer(context={'view':view})
        serializer.instance = node

        return serializer

    def test_change_single_field(self, WFJT_serializer):
        "Test that a single prompt field can be changed without affecting other fields"
        internal_value = WFJT_serializer.to_internal_value({'job_type': 'check'})
        assert internal_value['job_type'] == 'check'
        WFJT_serializer.instance.job_type = 'check'
        assert WFJT_serializer.instance.limit == 'webservers'

    def test_null_single_field(self, WFJT_serializer):
        "Test that a single prompt field can be removed without affecting other fields"
        internal_value = WFJT_serializer.to_internal_value({'job_type': None})
        assert internal_value['job_type'] is None
        WFJT_serializer.instance.job_type = None
        assert WFJT_serializer.instance.limit == 'webservers'


@mock.patch('awx.api.serializers.BaseSerializer.validate', lambda self, attrs: attrs)
class TestWorkflowJobTemplateNodeSerializerSurveyPasswords():

    @pytest.fixture
    def jt(self, survey_spec_factory):
        return JobTemplate(
            name='fake-jt',
            survey_enabled=True,
            survey_spec=survey_spec_factory(variables='var1', default_type='password'),
            project=Project('fake-proj'), project_id=42,
            inventory=Inventory('fake-inv'), inventory_id=42
        )

    def test_set_survey_passwords_create(self, jt):
        serializer = WorkflowJobTemplateNodeSerializer()
        wfjt = WorkflowJobTemplate(name='fake-wfjt')
        attrs = serializer.validate({
            'unified_job_template': jt,
            'workflow_job_template': wfjt,
            'extra_data': {'var1': 'secret_answer'}
        })
        assert 'survey_passwords' in attrs
        assert 'var1' in attrs['survey_passwords']
        assert attrs['extra_data']['var1'].startswith('$encrypted$')
        assert len(attrs['extra_data']['var1']) > len('$encrypted$')

    def test_set_survey_passwords_modify(self, jt):
        serializer = WorkflowJobTemplateNodeSerializer()
        wfjt = WorkflowJobTemplate(name='fake-wfjt')
        serializer.instance = WorkflowJobTemplateNode(
            workflow_job_template=wfjt,
            unified_job_template=jt
        )
        attrs = serializer.validate({
            'unified_job_template': jt,
            'workflow_job_template': wfjt,
            'extra_data': {'var1': 'secret_answer'}
        })
        assert 'survey_passwords' in attrs
        assert 'var1' in attrs['survey_passwords']
        assert attrs['extra_data']['var1'].startswith('$encrypted$')
        assert len(attrs['extra_data']['var1']) > len('$encrypted$')

    def test_use_db_answer(self, jt, mocker):
        serializer = WorkflowJobTemplateNodeSerializer()
        wfjt = WorkflowJobTemplate(name='fake-wfjt')
        serializer.instance = WorkflowJobTemplateNode(
            workflow_job_template=wfjt,
            unified_job_template=jt,
            extra_data={'var1': '$encrypted$foooooo'}
        )
        with mocker.patch('awx.main.models.mixins.decrypt_value', return_value='foo'):
            attrs = serializer.validate({
                'unified_job_template': jt,
                'workflow_job_template': wfjt,
                'extra_data': {'var1': '$encrypted$'}
            })
        assert 'survey_passwords' in attrs
        assert 'var1' in attrs['survey_passwords']
        assert attrs['extra_data']['var1'] == '$encrypted$foooooo'

    def test_accept_password_default(self, jt, mocker):
        '''
        If user provides "$encrypted$" without a corresponding DB value for the
        node, but survey question has a default, then variables are accepted
        with that particular var omitted so on launch time the default takes effect
        '''
        serializer = WorkflowJobTemplateNodeSerializer()
        wfjt = WorkflowJobTemplate(name='fake-wfjt')
        jt.survey_spec['spec'][0]['default'] = '$encrypted$bar'
        attrs = serializer.validate({
            'unified_job_template': jt,
            'workflow_job_template': wfjt,
            'extra_data': {'var1': '$encrypted$'}
        })
        assert 'survey_passwords' in attrs
        assert attrs['survey_passwords'] == {}
        assert attrs['extra_data'] == {}


@mock.patch('awx.api.serializers.WorkflowJobTemplateNodeSerializer.get_related', lambda x,y: {})
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
