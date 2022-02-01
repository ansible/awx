# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import logging
import heapq
from types import SimpleNamespace

# Django
from django.conf import settings

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
        if hasattr(other, 'hostname'):
            other = other.hostname
        return self.hostname == other

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

    def __getitem__(self, hostname):
        if hostname not in self.nodes:
            raise KeyError(f"No control node with hostname {hostname} found")
        for node in self.nodes:
            if node == hostname:
                return node

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

    def __str__(self):
        return f"{[n for n in self.nodes]}"


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
        return self.instances_partial[key]

    @staticmethod
    def find_largest_idle_instance(instances, capacity_type='execution'):
        largest_instance = None
        for i in instances:
            if i.node_type not in (capacity_type, 'hybrid'):
                continue
            if i.jobs_running == 0:
                if largest_instance is None:
                    largest_instance = i
                elif i.capacity > largest_instance.capacity:
                    largest_instance = i
        return largest_instance

    @staticmethod
    def fit_task_to_most_remaining_capacity_instance(task, instances):
        instance_most_capacity = None
        for i in instances:
            if i.node_type not in (task.capacity_type, 'hybrid'):
                continue
            if i.remaining_capacity >= task.task_impact and (
                instance_most_capacity is None or i.remaining_capacity > instance_most_capacity.remaining_capacity
            ):
                instance_most_capacity = i
        return instance_most_capacity

    def fit_task_to_instance(self, task, instance_group_name, ig_capacity_graph):
        # TODO: make heaps of execution nodes per instance group to be able
        # to pluck most capacity one off top
        return self.fit_task_to_most_remaining_capacity_instance(
            task, ig_capacity_graph.get(instance_group_name)['instances']
        ) or self.find_largest_idle_instance(ig_capacity_graph.get(instance_group_name)['instances'], capacity_type=task.capacity_type)

    def assign_task_to_execution_node(self, task, instance_group_name, ig_capacity_graph, execution_instance):
        # The fact that we are using this max function here tells me sometimes it is over assigned
        execution_instance.remaining_capacity = max(0, execution_instance.remaining_capacity - task.task_impact)
        execution_instance.jobs_running += 1

        # This part of consuming capacity on the ig_capacity_graph would stay the same
        ig_capacity_graph.consume_instance_group_capacity(task, instance_group_name, instance=execution_instance)
        ig_capacity_graph.get(instance_group_name)['dependency_graph'].add_job(task)

    def best_control_node_candidate(self):
        """Return a node with enough control capacity if it exists.

        Otherwise return None
        Does not actaully commit the capacity yet.
        Use assign_task_to_control_node to do that.
        """
        node = self.control_nodes.best_node()
        if self.has_sufficient_control_capacity(node):
            return node
        return None

    def has_sufficient_control_capacity(self, controller_node):
        if not isinstance(controller_node, PrioritizableNode) and isinstance(controller_node, str):
            controller_node = self.control_nodes[controller_node]
        return controller_node.remaining_capacity >= settings.AWX_CONTROL_NODE_TASK_IMPACT

    def consume_control_capacity(self, controller_node):
        if not isinstance(controller_node, PrioritizableNode) and isinstance(controller_node, str):
            controller_node = self.control_nodes[controller_node]
        controller_node.remaining_capacity -= settings.AWX_CONTROL_NODE_TASK_IMPACT
        self.control_nodes.update(controller_node)

    def assign_task_to_control_node(self, task, ig_capacity_graph, controller_node=None):
        """Account for task impact on a control node.

        If no control node is specified, find the best control node available.
        controller_node should be the string hostname

        If the node does not have enough remaining capacity for the task impact, return False
        """
        impact = settings.AWX_CONTROL_NODE_TASK_IMPACT
        if not controller_node:
            instance = self.control_nodes.best_node()
        else:
            instance = self.control_nodes[controller_node]

        if not self.has_sufficient_control_capacity(instance):
            logger.warning(f"Not enough control capacity for task {task.log_format} with task impact {impact} found on nodes {self.control_nodes}")
            return False

        for ig in self.instances_partial[instance.hostname].instance_groups:
            ig_capacity_graph.consume_instance_group_capacity(task, ig, instance=self.instances_partial[instance], impact=impact)
            ig_data = ig_capacity_graph.get(ig)
            if not ig_data['control_capacity'] - ig_data['consumed_control_capacity'] >= 0:
                # This whole block is kind of paranoid.
                # It covers a case that should really not happen since every time we assign a task to a node, we deduct from its instance group
                # capacity as well. If we never see this warning, maybe we can drop this code
                logger.warn(
                    f"""Somehow we had capacity on a control node {instance}
                        but not on its instance_group {ig} that has {ig_data['control_capacity']} control capacity
                        and {ig_data['consumed_control_capacity']} consumed control capacity"""
                )
        logger.debug(f"chose {instance} to be control node for {task.log_format}")
        self.consume_control_capacity(instance)
        return instance.hostname


class InstanceGroupCapacityGraph:
    def __init__(self, task_manager_instances):
        self.ig_capacity_graph = dict()
        breakdown = False
        for rampart_group in InstanceGroup.objects.prefetch_related('instances'):
            InstanceGroupManager.zero_out_group(self.ig_capacity_graph, rampart_group.name, breakdown)
            # Didn't move the init of DependencyGraph to InstanceGroupManager because of circular import
            self.ig_capacity_graph[rampart_group.name]['dependency_graph'] = DependencyGraph()
            for instance in rampart_group.instances.filter(enabled=True).order_by('hostname'):
                if instance.hostname in task_manager_instances.instances_partial:
                    self.ig_capacity_graph[rampart_group.name]['instances'].append(task_manager_instances[instance.hostname])
                for capacity_type in ('control', 'execution'):
                    if instance.node_type in (capacity_type, 'hybrid'):
                        self.ig_capacity_graph[rampart_group.name][f'{capacity_type}_capacity'] += instance.capacity

    def get(self, key):
        return self.ig_capacity_graph[key]

    def keys(self):
        return self.ig_capacity_graph.keys()

    def calculate_capacity_consumed(self, tasks):
        self.ig_capacity_graph = InstanceGroup.objects.capacity_values(tasks=tasks, graph=self.ig_capacity_graph)

    def consume_instance_group_capacity(self, task, instance_group, instance=None, impact=None):
        impact = impact if impact else task.task_impact
        logger.debug(
            '{} consumed {} capacity units from {} with prior total of {}'.format(
                task.log_format, impact, instance_group, self.ig_capacity_graph[instance_group]['consumed_capacity']
            )
        )
        self.ig_capacity_graph[instance_group]['consumed_capacity'] += impact
        for capacity_type in ('control', 'execution'):
            if instance is None or instance.node_type in ('hybrid', capacity_type):
                logger.debug(
                    '{} consumed {} {}_capacity units from {} with prior total of {}'.format(
                        task.log_format, impact, capacity_type, instance_group, self.ig_capacity_graph[instance_group][f'consumed_{capacity_type}_capacity']
                    )
                )
                self.ig_capacity_graph[instance_group][f'consumed_{capacity_type}_capacity'] += impact

    def get_remaining_capacity(self, instance_group, capacity_type='execution'):
        capacity = (
            self.ig_capacity_graph[instance_group][f'{capacity_type}_capacity'] - self.ig_capacity_graph[instance_group][f'consumed_{capacity_type}_capacity']
        )
        logger.debug(f'{instance_group} has {capacity} remaining capacity of type {capacity_type}')
        return capacity
