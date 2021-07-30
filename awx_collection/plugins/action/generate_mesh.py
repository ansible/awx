#!/usr/bin/python
# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.action import ActionBase
from datetime import datetime


class ActionModule(ActionBase):

    __res = """
    strict digraph "" {
    rankdir = LR
    subgraph cluster_0 {
        graph [label="Control Nodes", type=solid];
    """

    def generate_control_plane_topology(type=None, data=None):
        res = {}
        for index, control_node in enumerate(data[type]["hosts"]):
            res[control_node] = data[type]["hosts"][(index + 1) :]
        return res

    def generate_topology_from_input(type=None, data=None):
        res = {}
        if type is None:
            return None
        if type not in data.keys():
            return None
        for node in data[type]["hosts"]:
            # check to see if vertex exists
            if not node in res:
                res[node] = []
            if "peers" in (data["_meta"]["hostvars"][node].keys()):
                for peer in (data["_meta"]["hostvars"][node]["peers"]).split(","):
                    # handle groups
                    if peer in data.keys():
                        ## list comprehension to produce peers list. excludes circular reference to node
                        res[node] = res[node] + [x for x in data[peer]["hosts"] if x != node]
                    else:
                        res[node].append(peer)
        return res

    def deep_merge_dicts(lhs=None, rhs=None):

        local_lhs = lhs
        local_rhs = rhs

        if local_lhs is None or local_rhs is None:
            return
        for key, value in local_rhs.items():
            if key in local_lhs:
                local_lhs[key] = local_lhs[key] + value
            else:
                local_lhs[key] = value

        return local_lhs

    def generate_dot_syntax_from_dict(dict=None):

        if dict is None:
            return

        res = ""

        for label, nodes in dict.items():
            for node in nodes:
                res += '"{0}" -> "{1}";\n'.format(label, node)

        return res

    def detect_cycles(dict=None, data=None):

        if dict is None:
            return

        for key, nodes in dict.items():
            for node in nodes:
                if "peers" in (data["_meta"]["hostvars"][node].keys()):
                    if key in (data["_meta"]["hostvars"][node]["peers"]).split(","):
                        raise Exception("Cycle Detected Between [{0}] <-> [{1}]".format(key, node))
        return None

    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
            task_vars = dict()

        import sdb

        sdb.set_trace()

        result = super(ActionModule, self).run(tmp, task_vars)

        ret = dict()

        ret["hello"] = task_vars["hostvars"]

        return dict(stdout=dict(ret))
