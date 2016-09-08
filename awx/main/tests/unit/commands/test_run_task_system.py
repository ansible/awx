from awx.main.management.commands.run_task_system import (
    SimpleDAG,
    WorkflowDAG,
)
from awx.main.models import Job
from awx.main.models.workflow import WorkflowNode
import pytest

@pytest.fixture
def dag_root():
    dag = SimpleDAG()
    data = [
        {1: 1},
        {2: 2},
        {3: 3},
        {4: 4},
        {5: 5},
        {6: 6},
    ]
    # Add all the nodes to the DAG
    [dag.add_node(d) for d in data]

    dag.add_edge(data[0], data[1])
    dag.add_edge(data[2], data[3])
    dag.add_edge(data[4], data[5])
        
    return dag

@pytest.fixture
def dag_simple_edge_labels():
    dag = SimpleDAG()
    data = [
        {1: 1},
        {2: 2},
        {3: 3},
        {4: 4},
        {5: 5},
        {6: 6},
    ]
    # Add all the nodes to the DAG
    [dag.add_node(d) for d in data]

    dag.add_edge(data[0], data[1], 'one')
    dag.add_edge(data[2], data[3], 'two')
    dag.add_edge(data[4], data[5], 'three')

    return dag

'''
class TestSimpleDAG(object):
    def test_get_root_nodes(self, dag_root):
        leafs = dag_root.get_leaf_nodes() 

        roots = dag_root.get_root_nodes()

    def test_get_labeled_edges(self, dag_simple_edge_labels): 
        dag = dag_simple_edge_labels
        nodes = dag.get_dependencies(dag.nodes[0]['node_object'], 'one')
        nodes = dag.get_dependencies(dag.nodes[0]['node_object'], 'two')
'''

@pytest.fixture
def factory_node():
    def fn(id, status):
        wfn = WorkflowNode(id=id)
        if status:
            j = Job(status=status)
            wfn.job = j
        return wfn
    return fn

@pytest.fixture
def workflow_dag_level_2(factory_node):
    dag = WorkflowDAG()
    data = [
        factory_node(0, 'successful'),
        factory_node(1, 'successful'),
        factory_node(2, 'successful'),
        factory_node(3, None),
        factory_node(4, None),
        factory_node(5, None),
    ]
    [dag.add_node(d) for d in data]

    dag.add_edge(data[0], data[3], 'success_nodes')
    dag.add_edge(data[1], data[4], 'success_nodes')
    dag.add_edge(data[2], data[5], 'success_nodes')

    return (dag, data[3:6], False)

@pytest.fixture
def workflow_dag_multiple_roots(factory_node):
    dag = WorkflowDAG()
    data = [
        factory_node(1, None),
        factory_node(2, None),
        factory_node(3, None),
        factory_node(4, None),
        factory_node(5, None),
        factory_node(6, None),
    ]
    [dag.add_node(d) for d in data]

    dag.add_edge(data[0], data[3], 'success_nodes')
    dag.add_edge(data[1], data[4], 'success_nodes')
    dag.add_edge(data[2], data[5], 'success_nodes')

    expected = data[0:3]
    return (dag, expected, False)

@pytest.fixture
def workflow_dag_multiple_edges_labeled(factory_node):
    dag = WorkflowDAG()
    data = [
        factory_node(0, 'failed'),
        factory_node(1, None),
        factory_node(2, 'failed'),
        factory_node(3, None),
        factory_node(4, 'failed'),
        factory_node(5, None),
    ]
    [dag.add_node(d) for d in data]

    dag.add_edge(data[0], data[1], 'success_nodes')
    dag.add_edge(data[0], data[2], 'failure_nodes')
    dag.add_edge(data[2], data[3], 'success_nodes')
    dag.add_edge(data[2], data[4], 'failure_nodes')
    dag.add_edge(data[4], data[5], 'failure_nodes')

    expected = data[5:6]
    return (dag, expected, False)

@pytest.fixture
def workflow_dag_finished(factory_node):
    dag = WorkflowDAG()
    data = [
        factory_node(0, 'failed'),
        factory_node(1, None),
        factory_node(2, 'failed'),
        factory_node(3, None),
        factory_node(4, 'failed'),
        factory_node(5, 'successful'),
    ]
    [dag.add_node(d) for d in data]

    dag.add_edge(data[0], data[1], 'success_nodes')
    dag.add_edge(data[0], data[2], 'failure_nodes')
    dag.add_edge(data[2], data[3], 'success_nodes')
    dag.add_edge(data[2], data[4], 'failure_nodes')
    dag.add_edge(data[4], data[5], 'failure_nodes')

    expected = []
    return (dag, expected, True)

@pytest.fixture(params=['workflow_dag_multiple_roots', 'workflow_dag_level_2', 'workflow_dag_multiple_edges_labeled', 'workflow_dag_finished'])
def workflow_dag(request):
    return request.getfuncargvalue(request.param)

class TestWorkflowDAG():
    def test_bfs_nodes_to_run(self, workflow_dag):
        dag, expected, is_done = workflow_dag
        assert dag.bfs_nodes_to_run() == expected

    def test_is_workflow_done(self, workflow_dag):
        dag, expected, is_done = workflow_dag
        assert dag.is_workflow_done() == is_done

