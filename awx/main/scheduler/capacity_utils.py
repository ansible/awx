# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
import heapq
from types import SimpleNamespace

# Django
from django.utils.translation import ugettext_lazy as _, gettext_noop

# AWX
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.models import (
    Instance,
    InstanceGroup,
)


logger = logging.getLogger('awx.main.scheduler')


class PrioritizableControlNode:
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


class PrioritizedControlNodes:
    def __init__(self):
        self.control_nodes = set()

    def add(self, node):
        self.control_nodes.add(node)

    def update(self, node):
        """The __hash__ function for PrioritizableControlNodes just compares hostnames.

        We can add/remove the node to update object in PrioritizedControlNodes to have right capacity.
        """
        self.control_nodes.remove(node)
        self.control_nodes.add(node)

    # TODO: Maybe rename
    def assign_task_to_node(self, task, task_manager_instances={}, graph=None):
        """Find most available control instance and deduct task impact if we find it.

        If no node is available, return False
        """
        control_heap = list(self.control_nodes)
        heapq.heapify(control_heap)
        best_instance = heapq.nlargest(1, control_heap).pop()
        if best_instance.remaining_capacity < task.task_impact:
            return False

        if task_manager_instances and graph:
            for ig in task_manager_instances[best_instance.hostname].instance_groups:
                ig_data = graph[ig]
                # This should really not happen since every time we assign a task to a node, we deduct from its instance group
                # capacity as well. If we never see this, maybe we can drop this code
                if not ig_data['control_capacity'] - ig_data['consumed_control_capacity'] >= task.task_impact:
                    logger.warn(f"Somehow we had capacity on a control node {best_instance} but not on its instance_group {instance_group}")
                    return False
        logger.debug(f"chose {best_instance} to run {task.log_format}")
        best_instance.remaining_capacity -= task.task_impact
        self.update(best_instance)
        return best_instance


class TaskManagerInstances:
    def __init__(self):
        realinstances = Instance.objects.filter(hostname__isnull=False, enabled=True).exclude(node_type='hop').prefetch_related('rampart_groups')
        self.instances_partial = dict()
        self.control_nodes = PrioritizedControlNodes()

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
                self.control_nodes.add(PrioritizableControlNode(remaining_capacity=instance.remaining_capacity, hostname=instance.hostname))

    def __getitem__(self, key):
        return self.instances_partial.get(key)

    def init_graph(self, graph=dict()):
        for rampart_group in InstanceGroup.objects.prefetch_related('instances'):
            graph[rampart_group.name] = dict(
                graph=DependencyGraph(),
                execution_capacity=0,
                control_capacity=0,
                consumed_capacity=0,
                consumed_control_capacity=0,
                consumed_execution_capacity=0,
                instances=[],
            )
            for instance in rampart_group.instances.filter(enabled=True).order_by('hostname'):
                if instance.hostname in self.instances_partial:
                    graph[rampart_group.name]['instances'].append(self.instances_partial[instance.hostname])
                for capacity_type in ('control', 'execution'):
                    if instance.node_type in (capacity_type, 'hybrid'):
                        graph[rampart_group.name][f'{capacity_type}_capacity'] += instance.capacity
        return graph
