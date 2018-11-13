import pytest
import uuid

from awx.main.scheduler.dag_workflow import WorkflowDAG


class Job():
    def __init__(self, status='successful'):
        self.status = status


class WorkflowNodeBase(object):
    def __init__(self, id=None, job=None):
        self.id = id if id else uuid.uuid4()
        self.job = job


class WorkflowNodeDNR(WorkflowNodeBase):
    def __init__(self, do_not_run=False, **kwargs):
        super(WorkflowNodeDNR, self).__init__(**kwargs)
        self.do_not_run = do_not_run


class WorkflowNodeUJT(WorkflowNodeDNR):
    def __init__(self, unified_job_template=None, **kwargs):
        super(WorkflowNodeUJT, self).__init__(**kwargs)
        self.unified_job_template = unified_job_template


@pytest.fixture
def WorkflowNodeClass():
    return WorkflowNodeBase


@pytest.fixture
def wf_node_generator(mocker, WorkflowNodeClass):
    def fn(**kwargs):
        return WorkflowNodeClass(**kwargs)
    return fn


@pytest.fixture
def workflow_dag_1(wf_node_generator):
    g = WorkflowDAG()
    nodes = [wf_node_generator() for i in range(4)]
    map(lambda n: g.add_node(n), nodes)

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

        map(lambda n: g.add_node(n), wf_root_nodes + wf_leaf_nodes)

        '''
        Pair up a root node with a single child via an edge

        R1  R2 ... Rx
        |   |      |
        |   |      |
        C1  C2     Cx
        '''
        map(lambda (i, n): g.add_edge(wf_root_nodes[i], n, 'label'), enumerate(wf_leaf_nodes))
        return (g, wf_root_nodes, wf_leaf_nodes)


    def test_get_root_nodes(self, workflow_dag_root_children):
        (g, wf_root_nodes, ignore) = workflow_dag_root_children
        assert set([n.id for n in wf_root_nodes]) == set([n['node_object'].id for n in g.get_root_nodes()])


class TestDNR():
    @pytest.fixture
    def WorkflowNodeClass(self):
        return WorkflowNodeDNR

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
    def WorkflowNodeClass(self):
        return WorkflowNodeUJT

    @pytest.fixture
    def workflow_dag_2(self, workflow_dag_1):
        (g, nodes) = workflow_dag_1
        for n in nodes:
            n.unified_job_template = uuid.uuid4()
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

    def test_is_workflow_done(self, workflow_dag_2):
        g = workflow_dag_2[0]

        assert g.is_workflow_done() is False

    def test_is_workflow_done_failed(self, workflow_dag_failed):
        g = workflow_dag_failed[0]

        assert g.is_workflow_done() is True
        assert g.has_workflow_failed() is True
