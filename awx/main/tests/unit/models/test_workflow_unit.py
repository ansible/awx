import pytest

from awx.main.models.jobs import JobTemplate
from awx.main.models import Inventory, CredentialType, Credential, Project
from awx.main.models.workflow import (
    WorkflowJobTemplate, WorkflowJobTemplateNode,
    WorkflowJob, WorkflowJobNode
)
from unittest import mock


@pytest.fixture
def credential():
    ssh_type = CredentialType.defaults['ssh']()
    return Credential(
        id=43,
        name='example-cred',
        credential_type=ssh_type,
        inputs={'username': 'asdf', 'password': 'asdf'}
    )


class TestWorkflowJobInheritNodesMixin():
    class TestCreateWorkflowJobNodes():
        @pytest.fixture
        def job_templates(self):
            return [JobTemplate() for i in range(0, 10)]

        @pytest.fixture
        def job_template_nodes(self, job_templates):
            return [WorkflowJobTemplateNode(unified_job_template=job_templates[i]) for i in range(0, 10)]

        def test__create_workflow_job_nodes(self, mocker, job_template_nodes):
            workflow_job_node_create = mocker.patch('awx.main.models.WorkflowJobTemplateNode.create_workflow_job_node')

            workflow_job = WorkflowJob()
            workflow_job._create_workflow_nodes(job_template_nodes)

            for job_template_node in job_template_nodes:
                workflow_job_node_create.assert_any_call(workflow_job=workflow_job)

    class TestMapWorkflowJobNodes():
        @pytest.fixture
        def job_template_nodes(self):
            return [WorkflowJobTemplateNode(id=i) for i in range(0, 20)]

        @pytest.fixture
        def job_nodes(self):
            return [WorkflowJobNode(id=i) for i in range(100, 120)]

        def test__map_workflow_job_nodes(self, job_template_nodes, job_nodes, mocker):
            mixin = WorkflowJob()
            wj_node = WorkflowJobNode()
            mocker.patch('awx.main.models.workflow.WorkflowJobTemplateNode.create_workflow_job_node',
                         return_value=wj_node)

            node_ids_map = mixin._create_workflow_nodes(job_template_nodes, user=None)
            assert len(node_ids_map) == len(job_template_nodes)

            for i, job_template_node in enumerate(job_template_nodes):
                assert node_ids_map[job_template_node.id] == wj_node

    class TestInheritRelationship():
        @pytest.fixture
        def job_template_nodes(self, mocker):
            nodes = [mocker.MagicMock(id=i, pk=i) for i in range(0, 10)]

            for i in range(0, 9):
                nodes[i].success_nodes = mocker.MagicMock(
                    all=mocker.MagicMock(return_value=[mocker.MagicMock(id=i + 1, pk=i + 1)]))
                nodes[i].always_nodes = mocker.MagicMock(all=mocker.MagicMock(return_value=[]))
                nodes[i].failure_nodes = mocker.MagicMock(all=mocker.MagicMock(return_value=[]))
                new_wj_node = mocker.MagicMock(success_nodes=mocker.MagicMock())
                nodes[i].create_workflow_job_node = mocker.MagicMock(return_value=new_wj_node)

            return nodes

        @pytest.fixture
        def job_nodes(self, mocker):
            nodes = [mocker.MagicMock(id=i) for i in range(100, 110)]
            return nodes

        @pytest.fixture
        def job_nodes_dict(self, job_nodes):
            _map = {}
            for n in job_nodes:
                _map[n.id] = n
            return _map


        def test__inherit_relationship(self, mocker, job_template_nodes, job_nodes, job_nodes_dict):
            wj = WorkflowJob()

            node_ids_map = wj._create_workflow_nodes(job_template_nodes)
            wj._inherit_node_relationships(job_template_nodes, node_ids_map)

            for i in range(0, 8):
                node_ids_map[i].success_nodes.add.assert_any_call(node_ids_map[i + 1])


@pytest.fixture
def workflow_job_unit():
    return WorkflowJob(name='workflow', status='new')


@pytest.fixture
def workflow_job_template_unit():
    return WorkflowJobTemplate(name='workflow')


@pytest.fixture
def jt_ask(job_template_factory):
    # note: factory sets ask_xxxx_on_launch to true for inventory & credential
    jt = job_template_factory(name='example-jt', persisted=False).job_template
    jt.ask_variables_on_launch = True
    jt.ask_job_type_on_launch = True
    jt.ask_skip_tags_on_launch = True
    jt.ask_limit_on_launch = True
    jt.ask_tags_on_launch = True
    jt.ask_verbosity_on_launch = True
    return jt


@pytest.fixture
def project_unit():
    return Project(name='example-proj')


example_prompts = dict(job_type='check', job_tags='quack', limit='duck', skip_tags='oink')


@pytest.fixture
def job_node_no_prompts(workflow_job_unit, jt_ask):
    return WorkflowJobNode(workflow_job=workflow_job_unit, unified_job_template=jt_ask)


@pytest.fixture
def job_node_with_prompts(job_node_no_prompts, mocker):
    job_node_no_prompts.char_prompts = example_prompts
    job_node_no_prompts.inventory = Inventory(name='example-inv', id=45)
    job_node_no_prompts.inventory_id = 45
    return job_node_no_prompts


@pytest.fixture
def wfjt_node_no_prompts(workflow_job_template_unit, jt_ask):
    node = WorkflowJobTemplateNode(
        workflow_job_template=workflow_job_template_unit,
        unified_job_template=jt_ask
    )
    return node


@pytest.fixture
def wfjt_node_with_prompts(wfjt_node_no_prompts, mocker):
    wfjt_node_no_prompts.char_prompts = example_prompts
    wfjt_node_no_prompts.inventory = Inventory(name='example-inv')
    return wfjt_node_no_prompts


def test_node_getter_and_setters():
    node = WorkflowJobTemplateNode()
    node.job_type = 'check'
    assert node.char_prompts['job_type'] == 'check'
    assert node.job_type == 'check'


class TestWorkflowJobCreate:
    def test_create_no_prompts(self, wfjt_node_no_prompts, workflow_job_unit, mocker):
        mock_create = mocker.MagicMock()
        with mocker.patch('awx.main.models.WorkflowJobNode.objects.create', mock_create):
            wfjt_node_no_prompts.create_workflow_job_node(workflow_job=workflow_job_unit)
            mock_create.assert_called_once_with(
                all_parents_must_converge=False,
                extra_data={},
                survey_passwords={},
                char_prompts=wfjt_node_no_prompts.char_prompts,
                inventory=None,
                unified_job_template=wfjt_node_no_prompts.unified_job_template,
                workflow_job=workflow_job_unit,
                identifier=mocker.ANY)

    def test_create_with_prompts(self, wfjt_node_with_prompts, workflow_job_unit, credential, mocker):
        mock_create = mocker.MagicMock()
        with mocker.patch('awx.main.models.WorkflowJobNode.objects.create', mock_create):
            wfjt_node_with_prompts.create_workflow_job_node(
                workflow_job=workflow_job_unit
            )
            mock_create.assert_called_once_with(
                all_parents_must_converge=False,
                extra_data={},
                survey_passwords={},
                char_prompts=wfjt_node_with_prompts.char_prompts,
                inventory=wfjt_node_with_prompts.inventory,
                unified_job_template=wfjt_node_with_prompts.unified_job_template,
                workflow_job=workflow_job_unit,
                identifier=mocker.ANY)


@mock.patch('awx.main.models.workflow.WorkflowNodeBase.get_parent_nodes', lambda self: [])
class TestWorkflowJobNodeJobKWARGS:
    """
    Tests for building the keyword arguments that go into creating and
    launching a new job that corresponds to a workflow node.
    """
    kwargs_base = {'_eager_fields': {'launch_type': 'workflow'}}

    def test_null_kwargs(self, job_node_no_prompts):
        assert job_node_no_prompts.get_job_kwargs() == self.kwargs_base

    def test_inherit_workflow_job_and_node_extra_vars(self, job_node_no_prompts):
        job_node_no_prompts.extra_data = {"b": 98}
        workflow_job = job_node_no_prompts.workflow_job
        workflow_job.extra_vars = '{"a": 84}'
        assert job_node_no_prompts.get_job_kwargs() == dict(
            extra_vars={'a': 84, 'b': 98}, **self.kwargs_base)

    def test_char_prompts_and_res_node_prompts(self, job_node_with_prompts):
        # TBD: properly handle multicred credential assignment
        expect_kwargs = dict(
            inventory=job_node_with_prompts.inventory,
            **example_prompts)
        expect_kwargs.update(self.kwargs_base)
        assert job_node_with_prompts.get_job_kwargs() == expect_kwargs

    def test_reject_some_node_prompts(self, job_node_with_prompts):
        # TBD: properly handle multicred credential assignment
        job_node_with_prompts.unified_job_template.ask_inventory_on_launch = False
        job_node_with_prompts.unified_job_template.ask_job_type_on_launch = False
        expect_kwargs = dict(inventory=job_node_with_prompts.inventory,
                             **example_prompts)
        expect_kwargs.update(self.kwargs_base)
        expect_kwargs.pop('inventory')
        expect_kwargs.pop('job_type')
        assert job_node_with_prompts.get_job_kwargs() == expect_kwargs

    def test_no_accepted_project_node_prompts(self, job_node_no_prompts, project_unit):
        job_node_no_prompts.unified_job_template = project_unit
        assert job_node_no_prompts.get_job_kwargs() == self.kwargs_base

    def test_extra_vars_node_prompts(self, wfjt_node_no_prompts):
        wfjt_node_no_prompts.extra_vars = {'foo': 'bar'}
        assert wfjt_node_no_prompts.prompts_dict() == {'extra_vars': {'foo': 'bar'}}

    def test_string_extra_vars_node_prompts(self, wfjt_node_no_prompts):
        wfjt_node_no_prompts.extra_vars = '{"foo": "bar"}'
        assert wfjt_node_no_prompts.prompts_dict() == {'extra_vars': {'foo': 'bar'}}


def test_get_ask_mapping_integrity():
    assert list(WorkflowJobTemplate.get_ask_mapping().keys()) == ['extra_vars', 'inventory', 'limit', 'scm_branch']
