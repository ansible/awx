
# Python
import pytest

# AWX
from awx.main.models.workflow import WorkflowJob, WorkflowJobNode, WorkflowJobTemplateNode, WorkflowJobTemplate
from awx.main.models.jobs import Job
from awx.main.models.projects import ProjectUpdate
from awx.main.scheduler.dag_workflow import WorkflowDAG

# Django
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestWorkflowDAGFunctional(TransactionTestCase):
    def workflow_job(self):
        wfj = WorkflowJob.objects.create()
        nodes = [WorkflowJobNode.objects.create(workflow_job=wfj) for i in range(0, 5)]
        nodes[0].success_nodes.add(nodes[1])
        nodes[1].success_nodes.add(nodes[2])
        nodes[0].failure_nodes.add(nodes[3])
        nodes[3].failure_nodes.add(nodes[4])
        return wfj

    def test_build_WFJT_dag(self):
        '''
        Test that building the graph uses 4 queries
         1 to get the nodes
         3 to get the related success, failure, and always connections
        '''
        dag = WorkflowDAG()
        wfj = self.workflow_job()
        with self.assertNumQueries(4):
            dag._init_graph(wfj)


@pytest.mark.django_db
class TestWorkflowJob:
    @pytest.fixture
    def workflow_job(self, workflow_job_template_factory):
        wfjt = workflow_job_template_factory('blah').workflow_job_template
        wfj = WorkflowJob.objects.create(workflow_job_template=wfjt)

        nodes = [WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt) for i in range(0, 5)]

        nodes[0].success_nodes.add(nodes[1])
        nodes[1].success_nodes.add(nodes[2])

        nodes[0].failure_nodes.add(nodes[3])
        nodes[3].failure_nodes.add(nodes[4])

        return wfj

    def test_inherit_job_template_workflow_nodes(self, mocker, workflow_job):
        workflow_job.copy_nodes_from_original(original=workflow_job.workflow_job_template)

        nodes = WorkflowJob.objects.get(id=workflow_job.id).workflow_job_nodes.all().order_by('created')
        assert nodes[0].success_nodes.filter(id=nodes[1].id).exists()
        assert nodes[1].success_nodes.filter(id=nodes[2].id).exists()
        assert nodes[0].failure_nodes.filter(id=nodes[3].id).exists()
        assert nodes[3].failure_nodes.filter(id=nodes[4].id).exists()

    def test_inherit_ancestor_artifacts_from_job(self, project, mocker):
        """
        Assure that nodes along the line of execution inherit artifacts
        from both jobs ran, and from the accumulation of old jobs
        """
        # Related resources
        wfj = WorkflowJob.objects.create(name='test-wf-job')
        job = Job.objects.create(name='test-job', artifacts={'b': 43})
        # Workflow job nodes
        job_node = WorkflowJobNode.objects.create(workflow_job=wfj, job=job,
                                                  ancestor_artifacts={'a': 42})
        queued_node = WorkflowJobNode.objects.create(workflow_job=wfj)
        # Connect old job -> new job
        mocker.patch.object(queued_node, 'get_parent_nodes', lambda: [job_node])
        assert queued_node.get_job_kwargs()['extra_vars'] == {'a': 42, 'b': 43}
        assert queued_node.ancestor_artifacts == {'a': 42, 'b': 43}

    def test_inherit_ancestor_artifacts_from_project_update(self, project, mocker):
        """
        Test that the existence of a project update (no artifacts) does
        not break the flow of ancestor_artifacts
        """
        # Related resources
        wfj = WorkflowJob.objects.create(name='test-wf-job')
        update = ProjectUpdate.objects.create(name='test-update', project=project)
        # Workflow job nodes
        project_node = WorkflowJobNode.objects.create(workflow_job=wfj, job=update,
                                                      ancestor_artifacts={'a': 42, 'b': 43})
        queued_node = WorkflowJobNode.objects.create(workflow_job=wfj)
        # Connect project update -> new job
        mocker.patch.object(queued_node, 'get_parent_nodes', lambda: [project_node])
        assert queued_node.get_job_kwargs()['extra_vars'] == {'a': 42, 'b': 43}
        assert queued_node.ancestor_artifacts == {'a': 42, 'b': 43}


@pytest.mark.django_db
class TestWorkflowJobTemplate:
    @pytest.fixture
    def wfjt(self, workflow_job_template_factory, organization):
        wfjt = workflow_job_template_factory(
            'test', organization=organization).workflow_job_template
        wfjt.organization = organization
        nodes = [WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt) for i in range(0, 3)]
        nodes[0].success_nodes.add(nodes[1])
        nodes[1].failure_nodes.add(nodes[2])
        return wfjt

    def test_node_parentage(self, wfjt):
        # test success parent
        wfjt_node = wfjt.workflow_job_template_nodes.all()[1]
        parent_qs = wfjt_node.get_parent_nodes()
        assert len(parent_qs) == 1
        assert parent_qs[0] == wfjt.workflow_job_template_nodes.all()[0]
        # test failure parent
        wfjt_node = wfjt.workflow_job_template_nodes.all()[2]
        parent_qs = wfjt_node.get_parent_nodes()
        assert len(parent_qs) == 1
        assert parent_qs[0] == wfjt.workflow_job_template_nodes.all()[1]

    def test_topology_validator(self, wfjt):
        from awx.api.views import WorkflowJobTemplateNodeChildrenBaseList
        test_view = WorkflowJobTemplateNodeChildrenBaseList()
        nodes = wfjt.workflow_job_template_nodes.all()
        node_assoc = WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt)
        nodes[2].always_nodes.add(node_assoc)
        # test cycle validation
        assert test_view.is_valid_relation(node_assoc, nodes[0]) == {'Error': 'Cycle detected.'}
        # test multi-ancestor validation
        assert test_view.is_valid_relation(node_assoc, nodes[1]) == {'Error': 'Multiple parent relationship not allowed.'}
        # test mutex validation
        test_view.relationship = 'failure_nodes'
        node_assoc_1 = WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt)
        assert (test_view.is_valid_relation(nodes[2], node_assoc_1) ==
                {'Error': 'Cannot associate failure_nodes when always_nodes have been associated.'})

    def test_wfjt_copy(self, wfjt, job_template, inventory, admin_user):
        old_nodes = wfjt.workflow_job_template_nodes.all()
        node1 = old_nodes[1]
        node1.unified_job_template = job_template
        node1.save()
        node2 = old_nodes[2]
        node2.inventory = inventory
        node2.save()
        new_wfjt = wfjt.user_copy(admin_user)
        for fd in ['description', 'survey_spec', 'survey_enabled', 'extra_vars']:
            assert getattr(wfjt, fd) == getattr(new_wfjt, fd)
        assert new_wfjt.organization == wfjt.organization
        assert len(new_wfjt.workflow_job_template_nodes.all()) == 3
        nodes = new_wfjt.workflow_job_template_nodes.all()
        assert nodes[0].success_nodes.all()[0] == nodes[1]
        assert nodes[1].failure_nodes.all()[0] == nodes[2]
        assert nodes[1].unified_job_template == job_template
        assert nodes[2].inventory == inventory

    def test_wfjt_unique_together_with_org(self, organization):
        wfjt1 = WorkflowJobTemplate(name='foo', organization=organization)
        wfjt1.save()
        wfjt2 = WorkflowJobTemplate(name='foo', organization=organization)
        with pytest.raises(ValidationError):
            wfjt2.validate_unique()
        wfjt2 = WorkflowJobTemplate(name='foo', organization=None)
        wfjt2.validate_unique()


@pytest.mark.django_db
class TestWorkflowJobFailure:
    """
    Tests to re-implement if workflow failure status is introduced in
    a future Tower version.
    """
    @pytest.fixture
    def wfj(self):
        return WorkflowJob.objects.create(name='test-wf-job')

    def test_workflow_not_failed_unran_job(self, wfj):
        """
        Test that an un-ran node will not mark workflow job as failed
        """
        WorkflowJobNode.objects.create(workflow_job=wfj)
        assert not wfj._has_failed()

    def test_workflow_not_failed_successful_job(self, wfj):
        """
        Test that a sucessful node will not mark workflow job as failed
        """
        job = Job.objects.create(name='test-job', status='successful')
        WorkflowJobNode.objects.create(workflow_job=wfj, job=job)
        assert not wfj._has_failed()

    def test_workflow_not_failed_failed_job_but_okay(self, wfj):
        """
        Test that a failed node will not mark workflow job as failed
        """
        job = Job.objects.create(name='test-job', status='failed')
        WorkflowJobNode.objects.create(workflow_job=wfj, job=job)
        assert not wfj._has_failed()
