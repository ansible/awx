from collections import deque


class SimpleDAG(object):
    ''' A simple implementation of a directed acyclic graph '''

    def __init__(self):
        self.nodes = []
        self.root_nodes = set([])

        r'''
        Track node_obj->node index
        dict where key is a full workflow node object or whatever we are
        storing in ['node_object'] and value is an index to be used into
        self.nodes
        '''
        self.node_obj_to_node_index = dict()

        r'''
        Track per-node from->to edges

        i.e.
        {
            'success': {
                1: [2, 3],
                4: [2, 3],
            },
            'failed': {
                1: [5],
            }
        }
        '''
        self.node_from_edges_by_label = dict()

        r'''
        Track per-node reverse relationship (child to parent)

        i.e.
        {
            'success': {
                2: [1, 4],
                3: [1, 4],
            },
            'failed': {
                5: [1],
            }
        }
        '''
        self.node_to_edges_by_label = dict()

    def __contains__(self, obj):
        if self.node['node_object'] in self.node_obj_to_node_index:
            return True
        return False

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return self.nodes.__iter__()

    def generate_graphviz_plot(self, file_name="/awx_devel/graph.gv"):
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
            elif obj.do_not_run is True:
                color = 'gray'
            doc += "%s [color = %s]\n" % (
                run_status(n['node_object']),
                color
            )
        for label, edges in self.node_from_edges_by_label.items():
            for from_node, to_nodes in edges.items():
                for to_node in to_nodes:
                    doc += "%s -> %s [ label=\"%s\" ];\n" % (
                        run_status(self.nodes[from_node]['node_object']),
                        run_status(self.nodes[to_node]['node_object']),
                        label,
                    )
        doc += "}\n"
        gv_file = open(file_name, 'w')
        gv_file.write(doc)
        gv_file.close()

    def add_node(self, obj, metadata=None):
        if self.find_ord(obj) is None:
            '''
            Assume node is a root node until a child is added
            '''
            node_index = len(self.nodes)
            self.root_nodes.add(node_index)
            self.node_obj_to_node_index[obj] = node_index
            entry = dict(node_object=obj, metadata=metadata)
            self.nodes.append(entry)

    def add_edge(self, from_obj, to_obj, label):
        from_obj_ord = self.find_ord(from_obj)
        to_obj_ord = self.find_ord(to_obj)

        '''
        To node is no longer a root node
        '''
        self.root_nodes.discard(to_obj_ord)

        if from_obj_ord is None and to_obj_ord is None:
            raise LookupError("From object {} and to object {} not found".format(from_obj, to_obj))
        elif from_obj_ord is None:
            raise LookupError("From object not found {}".format(from_obj))
        elif to_obj_ord is None:
            raise LookupError("To object not found {}".format(to_obj))

        self.node_from_edges_by_label.setdefault(label, dict()) \
                                     .setdefault(from_obj_ord, [])
        self.node_to_edges_by_label.setdefault(label, dict()) \
                                   .setdefault(to_obj_ord, [])

        self.node_from_edges_by_label[label][from_obj_ord].append(to_obj_ord)
        self.node_to_edges_by_label[label][to_obj_ord].append(from_obj_ord)

    def find_ord(self, obj):
        return self.node_obj_to_node_index.get(obj, None)

    def _get_children_by_label(self, node_index, label):
        return [self.nodes[index] for index in
                self.node_from_edges_by_label.get(label, {})
                                             .get(node_index, [])]

    def get_children(self, obj, label=None):
        this_ord = self.find_ord(obj)
        nodes = []
        if label:
            return self._get_children_by_label(this_ord, label)
        else:
            nodes = []
            for label_obj in self.node_from_edges_by_label.keys():
                nodes.extend(self._get_children_by_label(this_ord, label_obj))
            return nodes

    def _get_parents_by_label(self, node_index, label):
        return [self.nodes[index] for index in
                self.node_to_edges_by_label.get(label, {})
                                           .get(node_index, [])]

    def get_parents(self, obj, label=None):
        this_ord = self.find_ord(obj)
        nodes = []
        if label:
            return self._get_parents_by_label(this_ord, label)
        else:
            nodes = []
            for label_obj in self.node_to_edges_by_label.keys():
                nodes.extend(self._get_parents_by_label(this_ord, label_obj))
            return nodes

    def get_root_nodes(self):
        return [self.nodes[index] for index in self.root_nodes]

    def has_cycle(self):
        node_objs = [node['node_object'] for node in self.get_root_nodes()]
        node_objs_visited = set([])
        path = set([])
        stack = node_objs
        res = False

        if len(self.nodes) != 0 and len(node_objs) == 0:
            return True

        while stack:
            node_obj = stack.pop()

            children = [node['node_object'] for node in self.get_children(node_obj)]
            children_to_add = list(filter(lambda node_obj: node_obj not in node_objs_visited, children))

            if children_to_add:
                if node_obj in path:
                    res = True
                    break
                path.add(node_obj)
                stack.append(node_obj)
                stack.extend(children_to_add)
            else:
                node_objs_visited.add(node_obj)
                path.discard(node_obj)
        return res

    def sort_nodes_topological(self):
        nodes_sorted = deque()
        obj_ids_processed = set([])

        def visit(node):
            obj = node['node_object']
            if obj.id in obj_ids_processed:
                return

            for child in self.get_children(obj):
                visit(child)
            obj_ids_processed.add(obj.id)
            nodes_sorted.appendleft(node)

        for node in self.nodes:
            obj = node['node_object']
            if obj.id in obj_ids_processed:
                continue

            visit(node)

        return nodes_sorted
