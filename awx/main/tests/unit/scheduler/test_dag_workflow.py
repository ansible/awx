import pytest
import uuid
import os

from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text

from awx.main.scheduler.dag_workflow import WorkflowDAG


class Job():
    def __init__(self, status='successful'):
        self.status = status


class WorkflowNode(object):
    def __init__(self, id=None, job=None, do_not_run=False, unified_job_template=None):
        self.id = id if id is not None else uuid.uuid4()
        self.job = job
        self.do_not_run = do_not_run
        self.unified_job_template = unified_job_template


@pytest.fixture
def wf_node_generator(mocker):
    pytest.count = 0

    def fn(**kwargs):
        wfn = WorkflowNode(id=pytest.count, unified_job_template=object(), **kwargs)
        pytest.count += 1
        return wfn
    return fn


@pytest.fixture
def workflow_dag_1(wf_node_generator):
    g = WorkflowDAG()
    nodes = [wf_node_generator() for i in range(4)]
    for n in nodes:
        g.add_node(n)

    r'''
            0
           /\
        S /  \
         /    \
         1    |
         |    |
       F |    | S
         |    |
         3    |
          \   |
         F \  |
            \/
             2
    '''
    g.add_edge(nodes[0], nodes[1], "success_nodes")
    g.add_edge(nodes[0], nodes[2], "success_nodes")
    g.add_edge(nodes[1], nodes[3], "failure_nodes")
    g.add_edge(nodes[3], nodes[2], "failure_nodes")
    return (g, nodes)


class TestWorkflowDAG():
    @pytest.fixture
    def workflow_dag_root_children(self, wf_node_generator):
        g = WorkflowDAG()
        wf_root_nodes = [wf_node_generator() for i in range(0, 10)]
        wf_leaf_nodes = [wf_node_generator() for i in range(0, 10)]

        for n in wf_root_nodes + wf_leaf_nodes:
            g.add_node(n)

        '''
        Pair up a root node with a single child via an edge

        R1  R2 ... Rx
        |   |      |
        |   |      |
        C1  C2     Cx
        '''
        for i, n in enumerate(wf_leaf_nodes):
            g.add_edge(wf_root_nodes[i], n, 'label')
        return (g, wf_root_nodes, wf_leaf_nodes)


    def test_get_root_nodes(self, workflow_dag_root_children):
        (g, wf_root_nodes, ignore) = workflow_dag_root_children
        assert set([n.id for n in wf_root_nodes]) == set([n['node_object'].id for n in g.get_root_nodes()])


class TestDNR():
    def test_mark_dnr_nodes(self, workflow_dag_1):
        (g, nodes) = workflow_dag_1

        r'''
               S0
               /\
            S /  \
             /    \
             1    |
             |    |
           F |    | S
             |    |
             3    |
              \   |
             F \  |
                \/
                2
        '''
        nodes[0].job = Job(status='successful')
        do_not_run_nodes = g.mark_dnr_nodes()
        assert 0 == len(do_not_run_nodes)

        r'''
               S0
               /\
            S /  \
             /    \
            S1    |
             |    |
           F |    | S
             |    |
         DNR 3    |
              \   |
             F \  |
                \/
                2
        '''
        nodes[1].job = Job(status='successful')
        do_not_run_nodes = g.mark_dnr_nodes()
        assert 1 == len(do_not_run_nodes)
        assert nodes[3] == do_not_run_nodes[0]


class TestIsWorkflowDone():
    @pytest.fixture
    def workflow_dag_2(self, workflow_dag_1):
        (g, nodes) = workflow_dag_1
        r'''
               S0
               /\
            S /  \
             /    \
            S1    |
             |    |
           F |    | S
             |    |
         DNR 3    |
              \   |
             F \  |
                \/
               W2
        '''
        nodes[0].job = Job(status='successful')
        g.mark_dnr_nodes()
        nodes[1].job = Job(status='successful')
        g.mark_dnr_nodes()
        nodes[2].job = Job(status='waiting')
        return (g, nodes)

    @pytest.fixture
    def workflow_dag_failed(self, workflow_dag_1):
        (g, nodes) = workflow_dag_1
        r'''
               S0
               /\
            S /  \
             /    \
            S1    |
             |    |
           F |    | S
             |    |
         DNR 3    |
              \   |
             F \  |
                \/
               F2
        '''
        nodes[0].job = Job(status='successful')
        g.mark_dnr_nodes()
        nodes[1].job = Job(status='successful')
        g.mark_dnr_nodes()
        nodes[2].job = Job(status='failed')
        return (g, nodes)

    @pytest.fixture
    def workflow_dag_canceled(self, wf_node_generator):
        g = WorkflowDAG()
        nodes = [wf_node_generator() for i in range(1)]
        for n in nodes:
            g.add_node(n)
        r'''
               F0
        '''
        nodes[0].job = Job(status='canceled')
        return (g, nodes)

    @pytest.fixture
    def workflow_dag_failure(self, workflow_dag_canceled):
        (g, nodes) = workflow_dag_canceled
        nodes[0].job.status = 'failed'
        return (g, nodes)

    def test_done(self, workflow_dag_2):
        g = workflow_dag_2[0]

        assert g.is_workflow_done() is False

    def test_workflow_done_and_failed(self, workflow_dag_failed):
        (g, nodes) = workflow_dag_failed

        assert g.is_workflow_done() is True
        assert g.has_workflow_failed() == \
            (True, smart_text(_("No error handle path for workflow job node(s) [({},{})] workflow job node(s)"
                                " missing unified job template and error handle path [].").format(nodes[2].id, nodes[2].job.status)))

    def test_is_workflow_done_no_unified_job_tempalte_end(self, workflow_dag_failed):
        (g, nodes) = workflow_dag_failed

        nodes[2].unified_job_template = None

        assert g.is_workflow_done() is True
        assert g.has_workflow_failed() == \
            (True, smart_text(_("No error handle path for workflow job node(s) [] workflow job node(s) missing"
             " unified job template and error handle path [{}].").format(nodes[2].id)))

    def test_is_workflow_done_no_unified_job_tempalte_begin(self, workflow_dag_1):
        (g, nodes) = workflow_dag_1

        nodes[0].unified_job_template = None
        g.mark_dnr_nodes()

        assert g.is_workflow_done() is True
        assert g.has_workflow_failed() == \
            (True, smart_text(_("No error handle path for workflow job node(s) [] workflow job node(s) missing"
             " unified job template and error handle path [{}].").format(nodes[0].id)))

    def test_canceled_should_fail(self, workflow_dag_canceled):
        (g, nodes) = workflow_dag_canceled

        assert g.has_workflow_failed() == \
            (True, smart_text(_("No error handle path for workflow job node(s) [({},{})] workflow job node(s)"
                                " missing unified job template and error handle path [].").format(nodes[0].id, nodes[0].job.status)))

    def test_failure_should_fail(self, workflow_dag_failure):
        (g, nodes) = workflow_dag_failure

        assert g.has_workflow_failed() == \
            (True, smart_text(_("No error handle path for workflow job node(s) [({},{})] workflow job node(s)"
                                " missing unified job template and error handle path [].").format(nodes[0].id, nodes[0].job.status)))


class TestBFSNodesToRun():
    @pytest.fixture
    def workflow_dag_canceled(self, wf_node_generator):
        g = WorkflowDAG()
        nodes = [wf_node_generator() for i in range(4)]
        for n in nodes:
            g.add_node(n)
        r'''
               C0
              / | \
           F / A|  \ S
            /   |   \
           1    2    3
        '''
        g.add_edge(nodes[0], nodes[1], "failure_nodes")
        g.add_edge(nodes[0], nodes[2], "always_nodes")
        g.add_edge(nodes[0], nodes[3], "success_nodes")
        nodes[0].job = Job(status='canceled')
        return (g, nodes)

    def test_cancel_still_runs_children(self, workflow_dag_canceled):
        (g, nodes) = workflow_dag_canceled
        g.mark_dnr_nodes()

        assert set([nodes[1], nodes[2]]) == set(g.bfs_nodes_to_run())


@pytest.mark.skip(reason="Run manually to re-generate doc images")
class TestDocsExample():
    @pytest.fixture
    def complex_dag(self, wf_node_generator):
        g = WorkflowDAG()
        nodes = [wf_node_generator() for i in range(10)]
        for n in nodes:
            g.add_node(n)

        g.add_edge(nodes[0], nodes[1], "failure_nodes")
        g.add_edge(nodes[0], nodes[2], "success_nodes")
        g.add_edge(nodes[0], nodes[3], "always_nodes")
        g.add_edge(nodes[1], nodes[4], "success_nodes")
        g.add_edge(nodes[1], nodes[5], "failure_nodes")

        g.add_edge(nodes[2], nodes[6], "failure_nodes")
        g.add_edge(nodes[3], nodes[6], "success_nodes")
        g.add_edge(nodes[4], nodes[6], "always_nodes")

        g.add_edge(nodes[6], nodes[7], "always_nodes")
        g.add_edge(nodes[6], nodes[8], "success_nodes")
        g.add_edge(nodes[6], nodes[9], "failure_nodes")

        return (g, nodes)

    def test_dnr_step(self, complex_dag):
        (g, nodes) = complex_dag
        base_dir = '/awx_devel'

        g.generate_graphviz_plot(file_name=os.path.join(base_dir, "workflow_step0.gv"))
        nodes[0].job = Job(status='successful')
        g.mark_dnr_nodes()
        g.generate_graphviz_plot(file_name=os.path.join(base_dir, "workflow_step1.gv"))
        nodes[2].job = Job(status='successful')
        nodes[3].job = Job(status='successful')
        g.mark_dnr_nodes()
        g.generate_graphviz_plot(file_name=os.path.join(base_dir, "workflow_step2.gv"))
        nodes[6].job = Job(status='failed')
        g.mark_dnr_nodes()
        g.generate_graphviz_plot(file_name=os.path.join(base_dir, "workflow_step3.gv"))
        nodes[7].job = Job(status='successful')
        nodes[9].job = Job(status='successful')
        g.mark_dnr_nodes()
        g.generate_graphviz_plot(file_name=os.path.join(base_dir, "workflow_step4.gv"))
