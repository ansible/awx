#!/usr/bin/python
# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from datetime import datetime

CONTROLLER_NODE_TYPES = ['control', 'hybrid']
EXECUTION_NODE_TYPES = ['execution', 'hop']

class ActionModule(ActionBase):
    __res = """
    strict digraph "" {
    rankdir = LR
    subgraph cluster_0 {
        graph [label="Control Nodes", type=solid];
    """

    def ge(data=None):
        res = {}
        for index, control_node in enumerate(data["control_nodes"]["hosts"]):
            res[control_node] = data["control_nodes"]["hosts"][(index + 1) :]
        return res

    def g(type=None, data=None):
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
                        res[node] = res[node] + [
                            x for x in data[peer]["hosts"] if x != node
                        ]
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
                    if key in (data["_meta"]["hostvars"][node]["peers"]).split(","): # comma seperated string
                        raise Exception(
                            "Cycle Detected Between [{0}] <-> [{1}]".format(key, node)
                        )

        return None

    def assert_verify_node_type(self, task_vars=None, group_name=None, valid_types=None,):
        """
        Members of given group_name must have a valid node_type.
        """
        for host in task_vars.get('groups').get(group_name):
            host_dict = dict(task_vars.get('hostvars').get(host))
            if 'node_type' not in host_dict.keys() or host_dict['node_type'] not in valid_types:
                raise AnsibleError(
                    'The host %s must have one of the valid node_types: %s' %
                    ( host, ', '.join(str(_) for _ in valid_types))
                )
        return


    def assert_unique_group(self, task_vars=None):
        """
        A given host cannot be part of the automationcontroller and execution_nodes group.
        """
        automation_group = task_vars.get('groups').get('automationcontroller')
        execution_nodes = task_vars.get('groups').get('execution_nodes')

        if automation_group and execution_nodes:
            intersection = list(set(automation_group) & set(execution_nodes))
            if intersection:
                raise AnsibleError(
                    'The following hosts cannot be members of both [automationcontroller] and [execution_nodes] groups: %s' %
                    ', '.join(str(_) for _ in intersection)
                )
        return

    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
            task_vars = dict()

        self.assert_unique_group(task_vars)
        self.assert_verify_node_type(task_vars, group_name='automationcontroller', valid_types=CONTROLLER_NODE_TYPES)
        self.assert_verify_node_type(task_vars, group_name='execution_nodes', valid_types=EXECUTION_NODE_TYPES)

        result = super(ActionModule, self).run(tmp, task_vars)
        # module_args = self._task.args.copy()
        # module_return = self._execute_module(
        #     module_name="ansible.builtin.ini",
        #     module_args=module_args,
        #     task_vars=task_vars,
        #     tmp=tmp,
        # )

        ret = dict()
        # remote_date = None
        # if not module_return.get("failed"):
        #     for key, value in module_return["ansible_facts"].items():
        #         if key == "ansible_date_time":
        #             remote_date = value["iso8601"]

        # if remote_date:
        #     remote_date_obj = datetime.strptime(remote_date, "%Y-%m-%dT%H:%M:%SZ")
        #     time_delta = datetime.utcnow() - remote_date_obj
        #     ret["delta_seconds"] = time_delta.seconds
        #     ret["delta_days"] = time_delta.days
        #     ret["delta_microseconds"] = time_delta.microseconds

        ret["hello"] = task_vars["hostvars"]

        return dict(stdout=dict(ret))

