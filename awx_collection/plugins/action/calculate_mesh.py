#!/usr/bin/python
# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from datetime import datetime
from collections import defaultdict


class ActionModule(ActionBase):

    _CONTROL_PLANE = "automationcontroller"
    _EXECUTION_PLANE = "execution_nodes"

    _NODE_VALID_TYPES = {
        "automationcontroller": {
            "types": frozenset(("control", "hybrid")),
            "default_type": "hybrid",
        },
        "execution_nodes": {
            "types": frozenset(("execution", "hop")),
            "default_type": "execution",
        },
    }

    _GENERATE_DOT_FILE_PARAM = "generate_dot_file"

    def generate_control_plane_topology(self, data):
        res = defaultdict(set)
        for index, control_node in enumerate(data["groups"][self._CONTROL_PLANE]):
            res[control_node] |= set(data["groups"][self._CONTROL_PLANE][(index + 1) :])
        return res

    def connect_peers(self, data):
        res = defaultdict(set)

        for group_name in self._NODE_VALID_TYPES:
            for node in data["groups"][group_name]:
                # if "peers" in data["hostvars"][node].keys():
                res[node]
                for peer in (
                    data["hostvars"][node].get("peers", "").split(",")
                ):  # to-do: make work with yaml list
                    # handle groups
                    if not peer:
                        continue
                    if peer in data["groups"]:
                        ## list comprehension to produce peers list. excludes circular reference to node
                        res[node] |= {x for x in data["groups"][peer] if x != node}
                    else:
                        res[node].add(peer)

        return res

    def deep_merge_dicts(self, *args):

        data = defaultdict(set)

        for d in args:
            for k, v in d.items():
                data[k] |= set(v)

        return dict(data)

    def generate_dot_syntax_from_dict(self, dict=None):

        if dict is None:
            return

        res = ""

        for label, nodes in dict.items():
            for node in nodes:
                res += '"{0}" -> "{1}";\n'.format(label, node)

        return res

    def detect_cycles(self, data):
        conflicts = set()
        for node, peers in data.items():  # k = host, v = set(hosts)
            for host in peers:
                if node in data.get(host, set()):
                    conflicts.add(frozenset((node, host)))
        if conflicts:
            conflict_str = ", ".join(f"[{n1}] <-> [{n2}]" for n1, n2 in conflicts)
            raise AnsibleError(
                fr"Two-way link(s) detected: {conflict_str} - Cannot have an inbound and outbound connection between the same two nodes"
            )

    def assert_node_type(self, host=None, vars=None, group_name=None, valid_types=None):
        """
        Members of given group_name must have a valid node_type.
        """
        if "node_type" not in vars.keys():
            return valid_types[group_name]["default_type"]

        if vars["node_type"] not in valid_types[group_name]["types"]:
            raise AnsibleError(
                "The host {0} must have one of the valid node_types: {1}".format(
                    host,
                    ", ".join(str(i) for i in valid_types[group_name]["types"]),
                )
            )
        return vars["node_type"]

    def assert_unique_group(self, task_vars=None):
        """
        A given host cannot be part of the automationcontroller and execution_nodes group.
        """
        automation_group = task_vars.get("groups").get("automationcontroller")
        execution_nodes = task_vars.get("groups").get("execution_nodes")

        if automation_group and execution_nodes:
            intersection = set(automation_group) & set(execution_nodes)
            if intersection:
                raise AnsibleError(
                    "The following hosts cannot be members of both [automationcontroller] and [execution_nodes] groups: {0}".format(
                        ", ".join(str(i) for i in intersection)
                    )
                )
        return

    def write_dot_graph_to_file(self, task_vars, filename="mesh.dot"):
        __RES = """
        strict digraph "" {
        rankdir = LR"""

        __CONTROL = """
        subgraph cluster_0 {
            graph [label="Control Nodes", type=solid];
        """

        control_nodes = self.generate_control_plane_topology(task_vars)
        execution_nodes = self.connect_peers(task_vars)

        __REST = ""

        # write control node relations
        for node in control_nodes:
            for peer in control_nodes[node]:
                __CONTROL += '"{0}" -> "{1}";\n'.format(node, peer)

        __CONTROL += "}\n"

        # write execution node relations
        for node in execution_nodes:
            for peer in execution_nodes[node]:
                __REST += '"{0}" -> "{1}";\n'.format(node, peer)

        __REST += "}\n"

        file = open(filename, mode="w")
        file.write(__RES + __CONTROL + __REST)
        file.close()

    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
            raise AnsibleError("task_vars is blank")

        super(ActionModule, self).run(tmp, task_vars)

        self.assert_unique_group(task_vars)

        # step 1 - generate a dict of peers connectivity
        peers = self.deep_merge_dicts(
            self.generate_control_plane_topology(task_vars),
            self.connect_peers(task_vars),
        )

        # step 2 - detect cycles; fail gracefully if found
        self.detect_cycles(peers)

        # step 3 - create a skeleton return object and fill it in with peers and node_type
        data = {}
        for group in [self._CONTROL_PLANE, self._EXECUTION_PLANE]:
            for host in task_vars.get("groups").get(group):
                _host_vars = dict(task_vars.get("hostvars").get(host))
                myhost_data = {}
                # myhost_data["name"] = host
                myhost_data["peers"] = sorted(peers[host])
                myhost_data["node_type"] = self.assert_node_type(
                    host=host,
                    vars=_host_vars,
                    group_name=group,
                    valid_types=self._NODE_VALID_TYPES,
                )
                data[host] = myhost_data

        # step 4 - generate dot file if user expressed interest in doing so
        if self._GENERATE_DOT_FILE_PARAM in self._task.args:
            self.write_dot_graph_to_file(
                task_vars, self._task.args[self._GENERATE_DOT_FILE_PARAM]
            )

        return dict(mesh=data)
