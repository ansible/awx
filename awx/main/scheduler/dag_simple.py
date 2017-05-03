
from awx.main.models import (
    Job,
    AdHocCommand,
    InventoryUpdate,
    ProjectUpdate,
    WorkflowJob,
)


class SimpleDAG(object):
    ''' A simple implementation of a directed acyclic graph '''

    def __init__(self):
        self.nodes = []
        self.edges = []

    def __contains__(self, obj):
        for node in self.nodes:
            if node['node_object'] == obj:
                return True
        return False

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return self.nodes.__iter__()

    def generate_graphviz_plot(self):
        def short_string_obj(obj):
            if type(obj) == Job:
                type_str = "Job"
            if type(obj) == AdHocCommand:
                type_str = "AdHocCommand"
            elif type(obj) == InventoryUpdate:
                type_str = "Inventory"
            elif type(obj) == ProjectUpdate:
                type_str = "Project"
            elif type(obj) == WorkflowJob:
                type_str = "Workflow"
            else:
                type_str = "Unknown"
            type_str += "%s" % str(obj.id)
            return type_str

        doc = """
        digraph g {
        rankdir = LR
        """
        for n in self.nodes:
            doc += "%s [color = %s]\n" % (
                short_string_obj(n['node_object']),
                "red" if n['node_object'].status == 'running' else "black",
            )
        for from_node, to_node, label in self.edges:
            doc += "%s -> %s [ label=\"%s\" ];\n" % (
                short_string_obj(self.nodes[from_node]['node_object']),
                short_string_obj(self.nodes[to_node]['node_object']),
                label,
            )
        doc += "}\n"
        gv_file = open('/tmp/graph.gv', 'w')
        gv_file.write(doc)
        gv_file.close()

    def add_node(self, obj, metadata=None):
        if self.find_ord(obj) is None:
            self.nodes.append(dict(node_object=obj, metadata=metadata))

    def add_edge(self, from_obj, to_obj, label=None):
        from_obj_ord = self.find_ord(from_obj)
        to_obj_ord = self.find_ord(to_obj)
        if from_obj_ord is None or to_obj_ord is None:
            raise LookupError("Object not found")
        self.edges.append((from_obj_ord, to_obj_ord, label))

    def add_edges(self, edgelist):
        for edge_pair in edgelist:
            self.add_edge(edge_pair[0], edge_pair[1], edge_pair[2])

    def find_ord(self, obj):
        for idx in range(len(self.nodes)):
            if obj == self.nodes[idx]['node_object']:
                return idx
        return None

    def get_dependencies(self, obj, label=None):
        antecedents = []
        this_ord = self.find_ord(obj)
        for node, dep, lbl in self.edges:
            if label:
                if node == this_ord and lbl == label:
                    antecedents.append(self.nodes[dep])
            else:
                if node == this_ord:
                    antecedents.append(self.nodes[dep])
        return antecedents

    def get_dependents(self, obj, label=None):
        decendents = []
        this_ord = self.find_ord(obj)
        for node, dep, lbl in self.edges:
            if label:
                if dep == this_ord and lbl == label:
                    decendents.append(self.nodes[node])
            else:
                if dep == this_ord:
                    decendents.append(self.nodes[node])
        return decendents

    def get_leaf_nodes(self):
        leafs = []
        for n in self.nodes:
            if len(self.get_dependencies(n['node_object'])) < 1:
                leafs.append(n)
        return leafs

    def get_root_nodes(self):
        roots = []
        for n in self.nodes:
            if len(self.get_dependents(n['node_object'])) < 1:
                roots.append(n)
        return roots
