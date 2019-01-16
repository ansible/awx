import pytest

from awx.main.scheduler.dag_simple import SimpleDAG


@pytest.fixture
def node_generator():
    def fn():
        return object()
    return fn


@pytest.fixture
def simple_cycle_1(node_generator):
    g = SimpleDAG()
    nodes = [node_generator() for i in range(4)]
    for n in nodes:
        g.add_node(n)

    r'''
            0
           /\
          /  \
         .    .
         1---.2
         .    |
         |    |
         -----|
              .
              3
    '''
    g.add_edge(nodes[0], nodes[1], "success_nodes")
    g.add_edge(nodes[0], nodes[2], "success_nodes")
    g.add_edge(nodes[2], nodes[3], "success_nodes")
    g.add_edge(nodes[2], nodes[1], "success_nodes")
    g.add_edge(nodes[1], nodes[2], "success_nodes")
    return (g, nodes)


def test_has_cycle(simple_cycle_1):
    (g, nodes) = simple_cycle_1

    assert g.has_cycle() is True
