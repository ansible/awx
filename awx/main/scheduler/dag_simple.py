

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
        def run_status(obj):
            dnr = "RUN"
            status = "NA"
            if hasattr(obj, 'job') and obj.job and hasattr(obj.job, 'status'):
                status = obj.job.status
            if hasattr(obj, 'do_not_run') and obj.do_not_run is True:
                dnr = "DNR"
            return "{}_{}_{}".format(dnr, status, obj.id)

        doc = """
        digraph g {
        rankdir = LR
        """
        for n in self.nodes:
            obj = n['node_object']
            status = "NA"
            if hasattr(obj, 'job') and obj.job:
                status = obj.job.status
            color = 'black'
            if status == 'successful':
                color = 'green'
            elif status == 'failed':
                color = 'red'
            doc += "%s [color = %s]\n" % (
                run_status(n['node_object']),
                color
            )
        for from_node, to_node, label in self.edges:
            doc += "%s -> %s [ label=\"%s\" ];\n" % (
                run_status(self.nodes[from_node]['node_object']),
                run_status(self.nodes[to_node]['node_object']),
                label,
            )
        doc += "}\n"
        gv_file = open('/awx_devel/graph.gv', 'w')
        gv_file.write(doc)
        gv_file.close()

    def add_node(self, obj, metadata=None):
        if self.find_ord(obj) is None:
            self.nodes.append(dict(node_object=obj, metadata=metadata))

    def add_edge(self, from_obj, to_obj, label=None):
        from_obj_ord = self.find_ord(from_obj)
        to_obj_ord = self.find_ord(to_obj)
        if from_obj_ord is None and to_obj_ord is None:
            raise LookupError("From object {} and to object not found".format(from_obj, to_obj))
        elif from_obj_ord is None:
            raise LookupError("From object not found {}".format(from_obj))
        elif to_obj_ord is None:
            raise LookupError("To object not found {}".format(to_obj))
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

    def has_cycle(self):
        node_objs = [node['node_object'] for node in self.get_root_nodes()]
        nodes_visited = set([])
        path = set([])
        stack = node_objs
        path_direction = 'DOWN'

        while stack:
            node_obj = stack.pop()

            children = self.get_dependencies(node_obj)
            for child in children:
                if child['node_object'] not in nodes_visited:
                    stack.append(child['node_object'])
            if node_obj in path:
                return True

            if not children:
                path_direction = 'UP'

            if path_direction == 'DOWN':
                path.add(node_obj)
            elif path_direction == 'UP':
                path.discard(node_obj)
        return False
