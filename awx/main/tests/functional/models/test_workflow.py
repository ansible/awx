
# Python
import pytest

# AWX
from awx.main.models.workflow import (
    WorkflowJob,
    WorkflowJobNode,
    WorkflowJobTemplateNode,
    WorkflowJobTemplate,
)
from awx.main.models.jobs import JobTemplate, Job
from awx.main.models.projects import ProjectUpdate
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.api.versioning import reverse
from awx.api.views import WorkflowJobTemplateNodeSuccessNodesList

# Django
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestWorkflowDAGFunctional(TransactionTestCase):
    def workflow_job(self, states=['new', 'new', 'new', 'new', 'new']):
        """
        Workflow topology:
               node[0]
                /\
              s/  \f
              /    \
           node[1] node[3]
             /       \
           s/         \f
           /           \
        node[2]       node[4]
        """
        wfj = WorkflowJob.objects.create()
        jt = JobTemplate.objects.create(name='test-jt')
        nodes = [WorkflowJobNode.objects.create(workflow_job=wfj, unified_job_template=jt) for i in range(0, 5)]
        for node, state in zip(nodes, states):
            if state:
                node.job = jt.create_job()
                node.job.status = state
                node.job.save()
                node.save()
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

    def test_workflow_done(self):
        wfj = self.workflow_job(states=['failed', None, None, 'successful', None])
        dag = WorkflowDAG(workflow_job=wfj)
        assert 3 == len(dag.mark_dnr_nodes())
        is_done = dag.is_workflow_done()
        has_failed, reason = dag.has_workflow_failed()
        self.assertTrue(is_done)
        self.assertFalse(has_failed)
        assert reason is None

        # verify that relaunched WFJ fails if a JT leaf is deleted
        for jt in JobTemplate.objects.all():
            jt.delete()
        relaunched = wfj.create_relaunch_workflow_job()
        dag = WorkflowDAG(workflow_job=relaunched)
        dag.mark_dnr_nodes()
        is_done = dag.is_workflow_done()
        has_failed, reason = dag.has_workflow_failed()
        self.assertTrue(is_done)
        self.assertTrue(has_failed)
        assert "Workflow job node {} related unified job template missing".format(wfj.workflow_nodes.all()[0].id)

    def test_workflow_fails_for_no_error_handler(self):
        wfj = self.workflow_job(states=['successful', 'failed', None, None, None])
        dag = WorkflowDAG(workflow_job=wfj)
        dag.mark_dnr_nodes()
        is_done = dag.is_workflow_done()
        has_failed = dag.has_workflow_failed()
        self.assertTrue(is_done)
        self.assertTrue(has_failed)

    def test_workflow_fails_leaf(self):
        wfj = self.workflow_job(states=['successful', 'successful', 'failed', None, None])
        dag = WorkflowDAG(workflow_job=wfj)
        dag.mark_dnr_nodes()
        is_done = dag.is_workflow_done()
        has_failed = dag.has_workflow_failed()
        self.assertTrue(is_done)
        self.assertTrue(has_failed)

    def test_workflow_not_finished(self):
        wfj = self.workflow_job(states=['new', None, None, None, None])
        dag = WorkflowDAG(workflow_job=wfj)
        dag.mark_dnr_nodes()
        is_done = dag.is_workflow_done()
        has_failed, reason = dag.has_workflow_failed()
        self.assertFalse(is_done)
        self.assertFalse(has_failed)
        assert reason is None


@pytest.mark.django_db
class TestWorkflowDNR():
    @pytest.fixture
    def workflow_job_fn(self):
        def fn(states=['new', 'new', 'new', 'new', 'new', 'new']):
            r"""
            Workflow topology:
                   node[0]
                    /   |
                  s     f
                  /     |
               node[1] node[3]
                 /      |
                s       f
               /        |
            node[2]    node[4]
               \        |
                s       f
                 \      |
                  node[5]
            """
            wfj = WorkflowJob.objects.create()
            jt = JobTemplate.objects.create(name='test-jt')
            nodes = [WorkflowJobNode.objects.create(workflow_job=wfj, unified_job_template=jt) for i in range(0, 6)]
            for node, state in zip(nodes, states):
                if state:
                    node.job = jt.create_job()
                    node.job.status = state
                    node.job.save()
                    node.save()
            nodes[0].success_nodes.add(nodes[1])
            nodes[1].success_nodes.add(nodes[2])
            nodes[0].failure_nodes.add(nodes[3])
            nodes[3].failure_nodes.add(nodes[4])
            nodes[2].success_nodes.add(nodes[5])
            nodes[4].failure_nodes.add(nodes[5])
            return wfj, nodes
        return fn

    def test_workflow_dnr_because_parent(self, workflow_job_fn):
        wfj, nodes = workflow_job_fn(states=['successful', None, None, None, None, None,])
        dag = WorkflowDAG(workflow_job=wfj)
        workflow_nodes = dag.mark_dnr_nodes()
        assert 2 == len(workflow_nodes)
        assert nodes[3] in workflow_nodes
        assert nodes[4] in workflow_nodes


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

    def test_inherit_ancestor_artifacts_from_job(self, job_template, mocker):
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
        queued_node = WorkflowJobNode.objects.create(workflow_job=wfj, unified_job_template=job_template)
        # Connect old job -> new job
        mocker.patch.object(queued_node, 'get_parent_nodes', lambda: [job_node])
        assert queued_node.get_job_kwargs()['extra_vars'] == {'a': 42, 'b': 43}
        assert queued_node.ancestor_artifacts == {'a': 42, 'b': 43}

    def test_inherit_ancestor_artifacts_from_project_update(self, project, job_template, mocker):
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
        queued_node = WorkflowJobNode.objects.create(workflow_job=wfj, unified_job_template=job_template)
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
        test_view = WorkflowJobTemplateNodeSuccessNodesList()
        nodes = wfjt.workflow_job_template_nodes.all()
        # test cycle validation
        print(nodes[0].success_nodes.get(id=nodes[1].id).failure_nodes.get(id=nodes[2].id))
        assert test_view.is_valid_relation(nodes[2], nodes[0]) == {'Error': 'Cycle detected.'}

    def test_always_success_failure_creation(self, wfjt, admin, get):
        wfjt_node = wfjt.workflow_job_template_nodes.all()[1]
        node = WorkflowJobTemplateNode.objects.create(workflow_job_template=wfjt)
        wfjt_node.always_nodes.add(node)
        assert len(node.get_parent_nodes()) == 1
        url = reverse('api:workflow_job_template_node_list') + str(wfjt_node.id) + '/'
        resp = get(url, admin)
        assert node.id in resp.data['always_nodes']

    def test_wfjt_unique_together_with_org(self, organization):
        wfjt1 = WorkflowJobTemplate(name='foo', organization=organization)
        wfjt1.save()
        wfjt2 = WorkflowJobTemplate(name='foo', organization=organization)
        with pytest.raises(ValidationError):
            wfjt2.validate_unique()
        wfjt2 = WorkflowJobTemplate(name='foo', organization=None)
        wfjt2.validate_unique()


@pytest.mark.django_db
def test_workflow_ancestors(organization):
    # Spawn order of templates grandparent -> parent -> child
    # create child WFJT and workflow job
    child = WorkflowJobTemplate.objects.create(organization=organization, name='child')
    child_job = WorkflowJob.objects.create(
        workflow_job_template=child,
        launch_type='workflow'
    )
    # create parent WFJT and workflow job, and link it up
    parent = WorkflowJobTemplate.objects.create(organization=organization, name='parent')
    parent_job = WorkflowJob.objects.create(
        workflow_job_template=parent,
        launch_type='workflow'
    )
    WorkflowJobNode.objects.create(
        workflow_job=parent_job,
        unified_job_template=child,
        job=child_job
    )
    # create grandparent WFJT and workflow job and link it up
    grandparent = WorkflowJobTemplate.objects.create(organization=organization, name='grandparent')
    grandparent_job = WorkflowJob.objects.create(
        workflow_job_template=grandparent,
        launch_type='schedule'
    )
    WorkflowJobNode.objects.create(
        workflow_job=grandparent_job,
        unified_job_template=parent,
        job=parent_job
    )
    # ancestors method gives a list of WFJT ids
    assert child_job.get_ancestor_workflows() == [parent, grandparent]


@pytest.mark.django_db
def test_workflow_ancestors_recursion_prevention(organization):
    # This is toxic database data, this tests that it doesn't create an infinite loop
    wfjt = WorkflowJobTemplate.objects.create(organization=organization, name='child')
    wfj = WorkflowJob.objects.create(
        workflow_job_template=wfjt,
        launch_type='workflow'
    )
    WorkflowJobNode.objects.create(
        workflow_job=wfj,
        unified_job_template=wfjt,
        job=wfj  # well, this is a problem
    )
    # mostly, we just care that this assertion finishes in finite time
    assert wfj.get_ancestor_workflows() == []
