import pytest

from awx.main.models.jobs import JobTemplate
from awx.main.models import Inventory, Credential, Project
from awx.main.models.workflow import (
    WorkflowJobTemplateNode, WorkflowJobInheritNodesMixin,
    WorkflowJob, WorkflowJobNode
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
            workflow_job_node_create = mocker.patch('awx.main.models.WorkflowJobNode.objects.create')

            mixin = WorkflowJobInheritNodesMixin()
            mixin._create_workflow_job_nodes(job_template_nodes)
            
            for job_template_node in job_template_nodes:
                workflow_job_node_create.assert_any_call(
                    workflow_job=mixin, unified_job_template=job_template_node.unified_job_template,
                    credential=None, inventory=None, char_prompts={})

    class TestMapWorkflowJobNodes():
        @pytest.fixture
        def job_template_nodes(self):
            return [WorkflowJobTemplateNode(id=i) for i in range(0, 20)]

        @pytest.fixture
        def job_nodes(self):
            return [WorkflowJobNode(id=i) for i in range(100, 120)]

        def test__map_workflow_job_nodes(self, job_template_nodes, job_nodes):
            mixin = WorkflowJobInheritNodesMixin()
            
            node_ids_map = mixin._map_workflow_job_nodes(job_template_nodes, job_nodes)
            assert len(node_ids_map) == len(job_template_nodes)

            for i, job_template_node in enumerate(job_template_nodes):
                assert node_ids_map[job_template_node.id] == job_nodes[i].id

    class TestInheritRelationship():
        @pytest.fixture
        def job_template_nodes(self, mocker):
            nodes = [mocker.MagicMock(id=i) for i in range(0, 10)]

            for i in range(0, 9):
                nodes[i].success_nodes = [mocker.MagicMock(id=i + 1)]

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
            mixin = WorkflowJobInheritNodesMixin()
            
            mixin._get_workflow_job_node_by_id = lambda x: job_nodes_dict[x]
            mixin._get_all_by_type = lambda x,node_type: x.success_nodes

            node_ids_map = mixin._map_workflow_job_nodes(job_template_nodes, job_nodes)

            for i, job_template_node in enumerate(job_template_nodes):
                mixin._inherit_relationship(job_template_node, job_nodes[i], node_ids_map, 'success_nodes')

            for i in range(0, 9):
                job_nodes[i].success_nodes.add.assert_any_call(job_nodes[i + 1])


@pytest.fixture
def workflow_job_unit():
    return WorkflowJob(name='workflow', status='new')

@pytest.fixture
def node_no_prompts(workflow_job_unit, job_template_factory):
    # note: factory sets ask_xxxx_on_launch to true for inventory & credential
    jt = job_template_factory(name='example-jt', persisted=False).job_template
    jt.ask_job_type_on_launch = True
    jt.ask_skip_tags_on_launch = True
    jt.ask_limit_on_launch = True
    jt.ask_tags_on_launch = True
    return WorkflowJobNode(workflow_job=workflow_job_unit, unified_job_template=jt)

@pytest.fixture
def project_unit():
    return Project(name='example-proj')

example_prompts = dict(job_type='scan', job_tags='quack', limit='duck', skip_tags='oink')

@pytest.fixture
def node_with_prompts(node_no_prompts):
    node_no_prompts.char_prompts = example_prompts
    inv = Inventory(name='example-inv')
    cred = Credential(name='example-inv', kind='ssh', username='asdf', password='asdf')
    node_no_prompts.inventory = inv
    node_no_prompts.credential = cred
    return node_no_prompts

class TestWorkflowJobNodeJobKWARGS:
    """
    Tests for building the keyword arguments that go into creating and
    launching a new job that corresponds to a workflow node.
    """

    def test_null_kwargs(self, node_no_prompts):
        assert node_no_prompts.get_job_kwargs() == {}

    def test_inherit_workflow_job_extra_vars(self, node_no_prompts):
        workflow_job = node_no_prompts.workflow_job
        workflow_job.extra_vars = '{"a": 84}'
        assert node_no_prompts.get_job_kwargs() == {'extra_vars': {'a': 84}}

    def test_char_prompts_and_res_node_prompts(self, node_with_prompts):
        assert node_with_prompts.get_job_kwargs() == dict(
            inventory=node_with_prompts.inventory,
            credential=node_with_prompts.credential,
            **example_prompts)

    def test_reject_some_node_prompts(self, node_with_prompts):
        node_with_prompts.unified_job_template.ask_inventory_on_launch = False
        node_with_prompts.unified_job_template.ask_job_type_on_launch = False
        expect_kwargs = dict(inventory=node_with_prompts.inventory,
                             credential=node_with_prompts.credential,
                             **example_prompts)
        expect_kwargs.pop('inventory')
        expect_kwargs.pop('job_type')
        assert node_with_prompts.get_job_kwargs() == expect_kwargs

    def test_no_accepted_project_node_prompts(self, node_with_prompts, project_unit):
        node_with_prompts.unified_job_template = project_unit
        assert node_with_prompts.get_job_kwargs() == {}


class TestWorkflowWarnings:
    """
    Tests of warnings that show user errors in the construction of a workflow
    """

    def test_warn_project_node_no_prompts(self, node_no_prompts, project_unit):
        node_no_prompts.unified_job_template = project_unit
        assert node_no_prompts.get_prompts_warnings() == {}

    def test_warn_project_node_reject_all_prompts(self, node_with_prompts, project_unit):
        node_with_prompts.unified_job_template = project_unit
        assert 'ignored' in node_with_prompts.get_prompts_warnings()
        assert 'all' in node_with_prompts.get_prompts_warnings()['ignored']

    def test_warn_reject_some_prompts(self, node_with_prompts):
        node_with_prompts.unified_job_template.ask_credential_on_launch = False
        node_with_prompts.unified_job_template.ask_job_type_on_launch = False
        assert 'ignored' in node_with_prompts.get_prompts_warnings()
        assert 'job_type' in node_with_prompts.get_prompts_warnings()['ignored']
        assert 'credential' in node_with_prompts.get_prompts_warnings()['ignored']
        assert len(node_with_prompts.get_prompts_warnings()['ignored']) == 2

    def test_warn_missing_fields(self, node_no_prompts):
        node_no_prompts.inventory = None
        assert 'missing' in node_no_prompts.get_prompts_warnings()
        assert 'inventory' in node_no_prompts.get_prompts_warnings()['missing']
        assert 'credential' in node_no_prompts.get_prompts_warnings()['missing']
        assert len(node_no_prompts.get_prompts_warnings()['missing']) == 2
