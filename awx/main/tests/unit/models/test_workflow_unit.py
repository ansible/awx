import pytest

from awx.main.models.jobs import JobTemplate
from awx.main.models.inventory import Inventory
from awx.main.models.credential import Credential
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
                workflow_job_node_create.assert_any_call(workflow_job=mixin, 
                                                         unified_job_template=job_template_node.unified_job_template)

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


class TestWorkflowJobHelperMethods:

    @pytest.fixture
    def workflow_job_unit(self):
        return WorkflowJob(name='workflow', status='new')

    @pytest.fixture
    def workflow_job_node_unit(self, workflow_job_unit, job_template_factory):
        # note: factory sets ask_inventory_on_launch to true when not provided
        jt = job_template_factory(name='example-jt', persisted=False).job_template
        return WorkflowJobNode(workflow_job=workflow_job_unit, unified_job_template=jt)

    def test_null_kwargs(self, workflow_job_node_unit):
        assert workflow_job_node_unit.get_job_kwargs() == {}

    def test_inherit_workflow_job_extra_vars(self, workflow_job_node_unit):
        workflow_job = workflow_job_node_unit.workflow_job
        workflow_job.extra_vars = '{"a": 84}'
        assert workflow_job_node_unit.get_job_kwargs() == {'extra_vars': {'a': 84}}

    def test_char_prompts_and_res_node_prompts(self, workflow_job_node_unit):
        barnyard_kwargs = dict(
            job_type='scan',
            job_tags='quack',
            limit='duck',
            skip_tags='oink'
        )
        workflow_job_node_unit.char_prompts = barnyard_kwargs
        inv = Inventory(name='example-inv')
        cred = Credential(name='example-inv', kind='ssh', username='asdf', password='asdf')
        workflow_job_node_unit.inventory = inv
        workflow_job_node_unit.credential = cred
        assert workflow_job_node_unit.get_job_kwargs() == dict(
            inventory=inv, credential=cred, **barnyard_kwargs)
