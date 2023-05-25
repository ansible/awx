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

    def __init__(self, obj, **kwargs):
        self.obj = obj
        self.node_type = obj.node_type
        self.consumed_capacity = 0
        self.capacity = obj.capacity
        self.hostname = obj.hostname
        self.jobs_running = 0

    def consume_capacity(self, impact, job_impact=False):
        self.consumed_capacity += impact
        if job_impact:
            self.jobs_running += 1

    @property
    def remaining_capacity(self):
        remaining = self.capacity - self.consumed_capacity
        if remaining < 0:
            return 0
        return remaining


class TaskManagerInstanceGroup:
    """A class representing minimal data the task manager needs to represent an InstanceGroup."""

    def __init__(self, obj, task_manager_instances=None, **kwargs):
        self.name = obj.name
        self.is_container_group = obj.is_container_group
        self.container_group_jobs = 0
        self.container_group_consumed_forks = 0
        _instances = obj.instances.all()
        # We want the list of TaskManagerInstance objects because these are shared across the TaskManagerInstanceGroup objects.
        # This way when we consume capacity on an instance that is in multiple groups, we tabulate across all the groups correctly.
        self.instances = [task_manager_instances[instance.hostname] for instance in _instances if instance.hostname in task_manager_instances]
        self.instance_hostnames = tuple([instance.hostname for instance in _instances if instance.hostname in task_manager_instances])
        self.max_concurrent_jobs = obj.max_concurrent_jobs
        self.max_forks = obj.max_forks
        self.control_task_impact = kwargs.get('control_task_impact', settings.AWX_CONTROL_NODE_TASK_IMPACT)

    def consume_capacity(self, task):
        """We only consume capacity on an instance group level if it is a container group. Otherwise we consume capacity on an instance level."""
        if self.is_container_group:
            self.container_group_jobs += 1
            self.container_group_consumed_forks += task.task_impact
        else:
            raise RuntimeError("We only track capacity for container groups at the instance group level. Otherwise, consume capacity on instances.")

    def get_remaining_instance_capacity(self):
        return sum(inst.remaining_capacity for inst in self.instances)

    def get_instance_capacity(self):
        return sum(inst.capacity for inst in self.instances)

    def get_consumed_instance_capacity(self):
        return sum(inst.consumed_capacity for inst in self.instances)

    def get_instance_jobs_running(self):
        return sum(inst.jobs_running for inst in self.instances)

    def get_jobs_running(self):
        if self.is_container_group:
            return self.container_group_jobs
        return sum(inst.jobs_running for inst in self.instances)

    def get_capacity(self):
        """This reports any type of capacity, including that of container group jobs.

        Container groups don't really have capacity, but if they have max_forks set,
        we can interperet that as how much capacity the user has defined them to have.
        """
        if self.is_container_group:
            return self.max_forks
        return self.get_instance_capacity()

    def get_consumed_capacity(self):
        if self.is_container_group:
            return self.container_group_consumed_forks
        return self.get_consumed_instance_capacity()

    def get_remaining_capacity(self):
        return self.get_capacity() - self.get_consumed_capacity()

    def has_remaining_capacity(self, task=None, control_impact=False):
        """Pass either a task or control_impact=True to determine if the IG has capacity to run the control task or job task."""
        task_impact = self.control_task_impact if control_impact else task.task_impact
        job_impact = 0 if control_impact else 1
        task_string = f"task {task.log_format} with impact of {task_impact}" if task else f"control task with impact of {task_impact}"

        # We only want to loop over instances if self.max_concurrent_jobs is set
        if self.max_concurrent_jobs == 0:
            # Override the calculated remaining capacity, because when max_concurrent_jobs == 0 we don't enforce any max
            remaining_jobs = 0
        else:
            remaining_jobs = self.max_concurrent_jobs - self.get_jobs_running() - job_impact

        # We only want to loop over instances if self.max_forks is set
        if self.max_forks == 0:
            # Override the calculated remaining capacity, because when max_forks == 0 we don't enforce any max
            remaining_forks = 0
        else:
            remaining_forks = self.max_forks - self.get_consumed_capacity() - task_impact

        if remaining_jobs < 0 or remaining_forks < 0:
            # A value less than zero means the task will not fit on the group
            if remaining_jobs < 0:
                logger.debug(f"{task_string} cannot fit on instance group {self.name} with {remaining_jobs} remaining jobs")
            if remaining_forks < 0:
                logger.debug(f"{task_string} cannot fit on instance group {self.name} with {remaining_forks} remaining forks")
            return False

        # Returning true means there is enough remaining capacity on the group to run the task (or no instance group level limits are being set)
        logger.debug(f"{task_string} can fit on instance group {self.name} with {remaining_forks} remaining forks and {remaining_jobs}")
        return True


class TaskManagerInstances:
    def __init__(self, instances=None, instance_fields=('node_type', 'capacity', 'hostname', 'enabled'), **kwargs):
        self.instances_by_hostname = dict()
        self.instance_groups_container_group_jobs = dict()
        self.instance_groups_container_group_consumed_forks = dict()
        self.control_task_impact = kwargs.get('control_task_impact', settings.AWX_CONTROL_NODE_TASK_IMPACT)

        if instances is None:
            instances = (
                Instance.objects.filter(hostname__isnull=False, node_state=Instance.States.READY, enabled=True)
                .exclude(node_type='hop')
                .only('node_type', 'node_state', 'capacity', 'hostname', 'enabled')
            )
        for instance in instances:
            self.instances_by_hostname[instance.hostname] = TaskManagerInstance(instance, **kwargs)

    def consume_capacity(self, task):
        control_instance = self.instances_by_hostname.get(task.controller_node, '')
        execution_instance = self.instances_by_hostname.get(task.execution_node, '')
        if execution_instance and execution_instance.node_type in ('hybrid', 'execution'):
            self.instances_by_hostname[task.execution_node].consume_capacity(task.task_impact, job_impact=True)
        if control_instance and control_instance.node_type in ('hybrid', 'control'):
            self.instances_by_hostname[task.controller_node].consume_capacity(self.control_task_impact)

    def __getitem__(self, hostname):
        return self.instances_by_hostname.get(hostname)

    def __contains__(self, hostname):
        return hostname in self.instances_by_hostname


class TaskManagerInstanceGroups:
    """A class representing minimal data the task manager needs to represent all the InstanceGroups."""

    def __init__(self, task_manager_instances=None, instance_groups=None, instance_groups_queryset=None, **kwargs):
        self.instance_groups = dict()
        self.task_manager_instances = task_manager_instances if task_manager_instances is not None else TaskManagerInstances()
        self.controlplane_ig = None
        self.pk_ig_map = dict()
        self.control_task_impact = kwargs.get('control_task_impact', settings.AWX_CONTROL_NODE_TASK_IMPACT)
        self.controlplane_ig_name = kwargs.get('controlplane_ig_name', settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME)

        if instance_groups is not None:  # for testing
            self.instance_groups = {ig.name: TaskManagerInstanceGroup(ig, self.task_manager_instances, **kwargs) for ig in instance_groups}
            self.pk_ig_map = {ig.pk: ig for ig in instance_groups}
        else:
            if instance_groups_queryset is None:
                instance_groups_queryset = InstanceGroup.objects.prefetch_related('instances').only(
                    'name', 'instances', 'max_concurrent_jobs', 'max_forks', 'is_container_group'
                )
            for instance_group in instance_groups_queryset:
                if instance_group.name == self.controlplane_ig_name:
                    self.controlplane_ig = instance_group
                self.instance_groups[instance_group.name] = TaskManagerInstanceGroup(instance_group, self.task_manager_instances, **kwargs)
                self.pk_ig_map[instance_group.pk] = instance_group

    def __getitem__(self, ig_name):
        return self.instance_groups.get(ig_name)

    def __contains__(self, ig_name):
        return ig_name in self.instance_groups

    def get_remaining_capacity(self, group_name):
        return self.instance_groups[group_name].get_remaining_instance_capacity()

    def get_consumed_capacity(self, group_name):
        return self.instance_groups[group_name].get_consumed_capacity()

    def get_jobs_running(self, group_name):
        return self.instance_groups[group_name].get_jobs_running()

    def get_capacity(self, group_name):
        return self.instance_groups[group_name].get_capacity()

    def get_instances(self, group_name):
        return self.instance_groups[group_name].instances

    def fit_task_to_most_remaining_capacity_instance(self, task, instance_group_name, impact=None, capacity_type=None, add_hybrid_control_cost=False):
        impact = impact if impact else task.task_impact
        capacity_type = capacity_type if capacity_type else task.capacity_type
        instance_most_capacity = None
        most_remaining_capacity = -1
        instances = self.instance_groups[instance_group_name].instances

        for i in instances:
            if i.node_type not in (capacity_type, 'hybrid'):
                continue
            would_be_remaining = i.remaining_capacity - impact
            # hybrid nodes _always_ control their own tasks
            if add_hybrid_control_cost and i.node_type == 'hybrid':
                would_be_remaining -= self.control_task_impact
            if would_be_remaining >= 0 and (instance_most_capacity is None or would_be_remaining > most_remaining_capacity):
                instance_most_capacity = i
                most_remaining_capacity = would_be_remaining
        return instance_most_capacity

    def find_largest_idle_instance(self, instance_group_name, capacity_type='execution'):
        largest_instance = None
        instances = self.instance_groups[instance_group_name].instances
        for i in instances:
            if i.node_type not in (capacity_type, 'hybrid'):
                continue
            if i.capacity <= 0:
                # We don't want to select an idle instance with 0 capacity
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


class TaskManagerModels:
    def __init__(self, **kwargs):
        # We want to avoid calls to settings over and over in loops, so cache this information here
        kwargs['control_task_impact'] = kwargs.get('control_task_impact', settings.AWX_CONTROL_NODE_TASK_IMPACT)
        kwargs['controlplane_ig_name'] = kwargs.get('controlplane_ig_name', settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME)
        self.instances = TaskManagerInstances(**kwargs)
        self.instance_groups = TaskManagerInstanceGroups(task_manager_instances=self.instances, **kwargs)

    @classmethod
    def init_with_consumed_capacity(cls, **kwargs):
        tmm = cls(**kwargs)
        tasks = kwargs.get('tasks', None)

        if tasks is None:
            instance_group_queryset = kwargs.get('instance_groups_queryset', None)
            # No tasks were provided, so we will fetch them from the database
            task_status_filter_list = kwargs.get('task_status_filter_list', ['running', 'waiting'])
            task_fields = kwargs.get('task_fields', ('task_impact', 'controller_node', 'execution_node', 'instance_group'))
            from awx.main.models import UnifiedJob

            if instance_group_queryset is not None:
                logger.debug("******************INSTANCE GROUP QUERYSET PASSED -- FILTERING TASKS ****************************")
                # Sometimes things like the serializer pass a queryset that looks at not all instance groups. in this case,
                # we also need to filter the tasks we look at
                tasks = UnifiedJob.objects.filter(status__in=task_status_filter_list, instance_group__in=[ig.id for ig in instance_group_queryset]).only(
                    *task_fields
                )
            else:
                # No instance group query set, look at all tasks in whole system
                tasks = UnifiedJob.objects.filter(status__in=task_status_filter_list).only(*task_fields)

        for task in tasks:
            tmm.consume_capacity(task)

        return tmm

    def consume_capacity(self, task):
        # Consume capacity on instances, which bubbles up to instance groups they are a member of
        self.instances.consume_capacity(task)

        # For container group jobs, additionally we must account for capacity consumed since
        # The container groups have no instances to look at to track how many jobs/forks are consumed
        if task.instance_group_id:
            if not task.instance_group_id in self.instance_groups.pk_ig_map.keys():
                logger.warn(
                    f"Task {task.log_format} assigned {task.instance_group_id} but this instance group not present in map of instance groups{self.instance_groups.pk_ig_map.keys()}"
                )
            else:
                ig = self.instance_groups.pk_ig_map[task.instance_group_id]
                if ig.is_container_group:
                    self.instance_groups[ig.name].consume_capacity(task)
