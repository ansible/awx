# Copyright (c) 2022 Ansible by Red Hat
# All Rights Reserved.
import logging

from django.conf import settings

from awx.main.models import (
    Instance,
    InstanceGroup,
)

logger = logging.getLogger('awx.main.scheduler')


class TaskManagerInstance:
    """A class representing minimal data the task manager needs to represent an Instance."""

    def __init__(self, obj):
        self.obj = obj
        self.node_type = obj.node_type
        self.consumed_capacity = 0
        self.capacity = obj.capacity
        self.hostname = obj.hostname

    def consume_capacity(self, impact):
        self.consumed_capacity += impact

    @property
    def remaining_capacity(self):
        remaining = self.capacity - self.consumed_capacity
        if remaining < 0:
            return 0
        return remaining


class TaskManagerInstances:
    def __init__(self, active_tasks, instances=None, instance_fields=['node_type', 'capacity', 'hostname', 'enabled']):
        self.instances_by_hostname = dict()
        self.instance_objects = []
        if instances is None:
            instances = Instance.objects.filter(hostname__isnull=False, enabled=True).exclude(node_type='hop').only(*instance_fields)
        for instance in instances:
            self.instances_by_hostname[instance.hostname] = TaskManagerInstance(instance)
            self.instance_objects.append(instance)

        # initialize remaining capacity based on currently waiting and running tasks
        for task in active_tasks:
            if task.status not in ['waiting', 'running']:
                continue
            control_instance = self.instances_by_hostname.get(task.controller_node, '')
            execution_instance = self.instances_by_hostname.get(task.execution_node, '')
            if execution_instance and execution_instance.node_type in ('hybrid', 'execution'):
                self.instances_by_hostname[task.execution_node].consume_capacity(task.task_impact)
            if control_instance and control_instance.node_type in ('hybrid', 'control'):
                self.instances_by_hostname[task.controller_node].consume_capacity(settings.AWX_CONTROL_NODE_TASK_IMPACT)

    def __getitem__(self, hostname):
        return self.instances_by_hostname.get(hostname)

    def __contains__(self, hostname):
        return hostname in self.instances_by_hostname


class TaskManagerInstanceGroups:
    """A class representing minimal data the task manager needs to represent an InstanceGroup."""

    def __init__(self, instances_by_hostname=None, instance_groups=None, instance_groups_queryset=None):
        self.instance_groups = dict()
        self.controlplane_ig = None
        self.pk_ig_map = dict()

        if instance_groups is not None:  # for testing
            self.instance_groups = instance_groups
        else:
            if instance_groups_queryset is None:
                instance_groups_queryset = InstanceGroup.objects.prefetch_related('instances').only('name', 'instances')
            for instance_group in instance_groups_queryset:
                if instance_group.name == settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME:
                    self.controlplane_ig = instance_group
                self.instance_groups[instance_group.name] = dict(
                    instances=[
                        instances_by_hostname[instance.hostname] for instance in instance_group.instances.all() if instance.hostname in instances_by_hostname
                    ],
                )
                self.pk_ig_map[instance_group.pk] = instance_group

    def get_remaining_capacity(self, group_name):
        instances = self.instance_groups[group_name]['instances']
        return sum(inst.remaining_capacity for inst in instances)

    def get_consumed_capacity(self, group_name):
        instances = self.instance_groups[group_name]['instances']
        return sum(inst.consumed_capacity for inst in instances)

    def fit_task_to_most_remaining_capacity_instance(self, task, instance_group_name, impact=None, capacity_type=None, add_hybrid_control_cost=False):
        impact = impact if impact else task.task_impact
        capacity_type = capacity_type if capacity_type else task.capacity_type
        instance_most_capacity = None
        most_remaining_capacity = -1
        instances = self.instance_groups[instance_group_name]['instances']

        for i in instances:
            if i.node_type not in (capacity_type, 'hybrid'):
                continue
            would_be_remaining = i.remaining_capacity - impact
            # hybrid nodes _always_ control their own tasks
            if add_hybrid_control_cost and i.node_type == 'hybrid':
                would_be_remaining -= settings.AWX_CONTROL_NODE_TASK_IMPACT
            if would_be_remaining >= 0 and (instance_most_capacity is None or would_be_remaining > most_remaining_capacity):
                instance_most_capacity = i
                most_remaining_capacity = would_be_remaining
        return instance_most_capacity

    def find_largest_idle_instance(self, instance_group_name, capacity_type='execution'):
        largest_instance = None
        instances = self.instance_groups[instance_group_name]['instances']
        for i in instances:
            if i.node_type not in (capacity_type, 'hybrid'):
                continue
            if (hasattr(i, 'jobs_running') and i.jobs_running == 0) or i.remaining_capacity == i.capacity:
                if largest_instance is None:
                    largest_instance = i
                elif i.capacity > largest_instance.capacity:
                    largest_instance = i
        return largest_instance

    def get_instance_groups_from_task_cache(self, task):
        igs = []
        if task.preferred_instance_groups_cache:
            for pk in task.preferred_instance_groups_cache:
                ig = self.pk_ig_map.get(pk, None)
                if ig:
                    igs.append(ig)
                else:
                    logger.warn(f"Unknown instance group with pk {pk} for task {task}")
        if len(igs) == 0:
            logger.warn(f"No instance groups in cache exist, defaulting to global instance groups for task {task}")
            return task.global_instance_groups
        return igs
