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
    def __init__(self, remaining_capacity, hostname, jobs_running):
        self.remaining_capacity = remaining_capacity
        self.hostname = hostname
        self.jobs_running = jobs_running

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
            raise KeyError(f"No node with hostname {hostname} found")
        for node in self.nodes:
            if node == hostname:
                return node

    def __contains__(self, other):
        return other in self.nodes

    def update(self, node):
        """The __hash__ function for PrioritizableNodes just compares hostnames.

        We can add/remove the node to update object in PrioritizedNodes to have right capacity.
        """
        self.nodes.remove(node)
        self.nodes.add(node)

    def best_node(self):
        if self.nodes:
            heap = list(self.nodes)
            heapq.heapify(heap)
            return heapq.nlargest(1, heap).pop()
        return None

    def __str__(self):
        return f"{[n for n in self.nodes]}"


class TaskManagerInstances:
    def __init__(self):
        self.instances_partial = dict()
        self.nodes = {'control_nodes': {}, 'hybrid_nodes': {}, 'execution_nodes': {}}
        self.ig_dependency_graphs = dict()
        self.controlplane_ig = None

        for rampart_group in InstanceGroup.objects.prefetch_related('instances'):
            self.ig_dependency_graphs[rampart_group.name] = DependencyGraph()
            if rampart_group.name == 'controlplane':
                self.controlplane_ig = rampart_group
            for node_type in ('hybrid', 'control', 'execution'):
                if not rampart_group.name in self.nodes[f'{node_type}_nodes']:
                    self.nodes[f'{node_type}_nodes'][rampart_group.name] = PrioritizedNodes()
            for instance in rampart_group.instances.filter(hostname__isnull=False, enabled=True).exclude(node_type='hop').order_by('hostname'):
                self.nodes[f'{instance.node_type}_nodes'][rampart_group.name].add(
                    # TODO: Don't call the Instance.remaining_capacity property because this queries all the running and
                    # waiting tasks on this instance, which is expensive. Generally there are more tasks than instances
                    # so it costs less to loop over instances multiple times than query all running and waiting tasks multiple times
                    # Instead we may need to init with total capacity, and then later when
                    # we have the tasks update the nodes w/ the right remaining capacity. This more closly matches
                    # what we used to do tracking capacity remaining on the instance group
                    PrioritizableNode(remaining_capacity=instance.remaining_capacity, hostname=instance.hostname, jobs_running=instance.jobs_running)
                )
                if instance.hostname not in self.instances_partial:
                    self.instances_partial[instance.hostname] = SimpleNamespace(
                        obj=instance,
                        node_type=instance.node_type,
                        hostname=instance.hostname,
                        instance_groups=[rampart_group.name],
                    )
                else:
                    self.instances_partial[instance.hostname].instance_groups.append(rampart_group.name)
            logger.debug(f"Control nodes in {rampart_group.name}: {self.nodes['control_nodes'][rampart_group.name]}")
            logger.debug(f"Hybrid nodes in {rampart_group.name}: {self.nodes['hybrid_nodes'][rampart_group.name]}")
            logger.debug(f"Execution nodes {rampart_group.name}: {self.nodes['execution_nodes'][rampart_group.name]}")

    def __getitem__(self, key):
        return self.instances_partial[key]

    def find_largest_idle_instance(self, instance_group, capacity_type='execution'):
        largest_instance = None
        best_node = None
        if capacity_type != 'execution':
            for nodes in ('hybrid_nodes', 'execution_nodes'):
                if instance_group in self.nodes[nodes]:
                    best_node = self.nodes[nodes][instance_group].best_node()
            if best_node and best_node.jobs_running == 0:
                largest_instace = best_node
        else:
            # looking for control capacity
            for nodes in ('hybrid_nodes', 'control_nodes'):
                if instance_group in self.nodes[nodes]:
                    best_node = self.nodes[nodes][instance_group].best_node()
                    if best_node:
                        break
            if best_node and best_node.jobs_running == 0:
                largest_instace = best_node
        if largest_instance:
            return largest_instance.hostname
        return None

    def fit_task_to_most_remaining_capacity_instance(self, task, instance_group, capacity_type, impact=None):
        instance_most_capacity = None
        best_node = None
        impact = impact if impact else task.task_impact
        if capacity_type == 'execution':
            for nodes in ('hybrid_nodes', 'execution_nodes'):
                if instance_group in self.nodes[nodes]:
                    best_node = self.nodes[nodes][instance_group].best_node()
                    if best_node:
                        break
            if best_node and best_node.remaining_capacity >= impact:
                instance_most_capacity = best_node
        else:
            # looking for control capacity
            for nodes in ('hybrid_nodes', 'control_nodes'):
                if instance_group in self.nodes[nodes]:
                    best_node = self.nodes[nodes][instance_group].best_node()
                    if best_node:
                        break
            if best_node and best_node.remaining_capacity >= impact:
                instance_most_capacity = best_node
        if instance_most_capacity:
            return instance_most_capacity.hostname
        return None

    def fit_task_to_instance(self, task, instance_group_name, capacity_type=None, impact=None):
        # TODO: make heaps of execution nodes per instance group to be able
        # to pluck most capacity one off top
        capacity_type = capacity_type if capacity_type else task.capacity_type
        return self.fit_task_to_most_remaining_capacity_instance(task, instance_group_name, capacity_type, impact) or self.find_largest_idle_instance(
            instance_group_name, capacity_type
        )

    def assign_task_to_node(self, task, instance_group_name, instance, impact=None):
        impact = impact if impact else task.task_impact
        if hasattr(instance, 'hostname'):
            instance = instance.hostname
        logger.warn(f"instances_partial is {self.instances_partial}")
        node_type = self.instances_partial[instance].node_type
        logger.warn(f"Assigning task {task.log_format} to {instance} of node type {node_type}.")
        if node_type in ('hybrid', 'control') and 'controlplane' not in self.instances_partial[instance].instance_groups:
            logger.error(
                f"Error assigning task {task.log_format} to {instance} of node type {node_type}. All hybrid and control nodes must be members of the 'controlplane' instance group"
            )
            raise AttributeError(f"{instance} has node type {node_type} but is not in the 'controlplane' instance group")
        instance = self.nodes[f'{node_type}_nodes'][instance_group_name][instance]
        # We are using this max function here because there are situations that we accept some overassignment
        instance.remaining_capacity = max(0, instance.remaining_capacity - impact)
        instance.jobs_running += 1
        node_type = self.instances_partial[instance.hostname].node_type
        for ig in self.instances_partial[instance].instance_groups:
            self.nodes[f'{node_type}_nodes'][ig].update(instance)
            self.ig_dependency_graphs[ig].add_job(task)

    def instance_groups(self):
        return self.ig_dependency_graphs.keys()
