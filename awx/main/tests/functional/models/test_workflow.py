
# Python
import pytest

# AWX
from awx.main.models.workflow import WorkflowJob, WorkflowJobNode, WorkflowJobTemplateNode
from awx.main.models.jobs import Job
from awx.main.models.projects import ProjectUpdate

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
        workflow_job.inherit_job_template_workflow_nodes()

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
    def wfjt(self, workflow_job_template_factory):
        wfjt = workflow_job_template_factory('test').workflow_job_template
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
