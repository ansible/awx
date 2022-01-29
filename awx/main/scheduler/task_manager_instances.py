# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
import heapq
from types import SimpleNamespace

# AWX
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.managers import InstanceGroupManager
from awx.main.models import (
    Instance,
    InstanceGroup,
)


logger = logging.getLogger('awx.main.scheduler')


class PrioritizableNode:
    def __init__(self, remaining_capacity, hostname):
        self.remaining_capacity = remaining_capacity
        self.hostname = hostname

    def __gt__(self, other):
        return self.remaining_capacity > other.remaining_capacity

    def __lt__(self, other):
        return self.remaining_capacity < other.remaining_capacity

    def __eq__(self, other):
        return self.hostname == other.hostname

    def __hash__(self):
        return hash(self.hostname)

    def __str__(self):
        return f"{self.hostname}: {self.remaining_capacity} remaining capacity"

    def __repr__(self):
        return self.__str__()


class PrioritizedNodes:
    def __init__(self):
        self.nodes = set()

    def add(self, node):
        self.nodes.add(node)

    def update(self, node):
        """The __hash__ function for PrioritizableNodes just compares hostnames.

        We can add/remove the node to update object in PrioritizedNodes to have right capacity.
        """
        self.nodes.remove(node)
        self.nodes.add(node)

    def best_node(self):
        heap = list(self.nodes)
        heapq.heapify(heap)
        return heapq.nlargest(1, heap).pop()


class TaskManagerInstances:
    def __init__(self):
        realinstances = Instance.objects.filter(hostname__isnull=False, enabled=True).exclude(node_type='hop').prefetch_related('rampart_groups')
        self.instances_partial = dict()
        self.control_nodes = PrioritizedNodes()

        for instance in realinstances:
            self.instances_partial[instance.hostname] = SimpleNamespace(
                obj=instance,
                node_type=instance.node_type,
                remaining_capacity=instance.remaining_capacity,
                capacity=instance.capacity,
                jobs_running=instance.jobs_running,
                hostname=instance.hostname,
                instance_groups=[ig.name for ig in instance.rampart_groups.all()],
            )
            if instance.node_type in ('control', 'hybrid'):
                self.control_nodes.add(PrioritizableNode(remaining_capacity=instance.remaining_capacity, hostname=instance.hostname))

    def __getitem__(self, key):
        return self.instances_partial.get(key)

    def init_ig_capacity_graph(self, graph=dict()):
        breakdown = False
        for rampart_group in InstanceGroup.objects.prefetch_related('instances'):
            InstanceGroupManager.zero_out_group(graph, rampart_group.name, breakdown)
            # Didn't move the init of DependencyGraph to InstanceGroupManager because of circular import
            graph[rampart_group.name]['dependency_graph'] = DependencyGraph()
            for instance in rampart_group.instances.filter(enabled=True).order_by('hostname'):
                if instance.hostname in self.instances_partial:
                    graph[rampart_group.name]['instances'].append(self.instances_partial[instance.hostname])
                for capacity_type in ('control', 'execution'):
                    if instance.node_type in (capacity_type, 'hybrid'):
                        graph[rampart_group.name][f'{capacity_type}_capacity'] += instance.capacity
        return graph

    def assign_task_to_control_node(self, task, ig_capacity_graph=None):
        """Find most available control instance and deduct task impact if we find it.

        If no node is available, return False
        """
        best_instance = self.control_nodes.best_node()
        if best_instance.remaining_capacity < task.task_impact:
            return False

        if ig_capacity_graph:
            # This whole block is kind of paranoid.
            # It covers a case that should really not happen since every time we assign a task to a node, we deduct from its instance group
            # capacity as well. If we never see this warning, maybe we can drop this code
            for ig in self.instances_partial[best_instance.hostname].instance_groups:
                ig_data = ig_capacity_graph[ig]
                if not ig_data['control_capacity'] - ig_data['consumed_control_capacity'] >= task.task_impact:
                    logger.warn(f"Somehow we had capacity on a control node {best_instance} but not on its instance_group {ig}")
                    return False
        logger.debug(f"chose {best_instance} to be control node for {task.log_format}")
        best_instance.remaining_capacity -= task.task_impact
        self.control_nodes.update(best_instance)
        return best_instance
