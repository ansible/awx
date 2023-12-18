# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import timedelta
import logging
import uuid
import json
import time
import sys
import signal

# Django
from django.db import transaction
from django.utils.translation import gettext_lazy as _, gettext_noop
from django.utils.timezone import now as tz_now
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from ansible_base.utils.models import get_type_for_model

# AWX
from awx.main.dispatch.reaper import reap_job
from awx.main.models import (
    Instance,
    InventorySource,
    InventoryUpdate,
    Job,
    Project,
    UnifiedJob,
    WorkflowApproval,
    WorkflowJob,
    WorkflowJobNode,
    WorkflowJobTemplate,
)
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.main.utils.pglock import advisory_lock
from awx.main.utils import (
    ScheduleTaskManager,
    ScheduleWorkflowManager,
)
from awx.main.utils.common import task_manager_bulk_reschedule, is_testing
from awx.main.signals import disable_activity_stream
from awx.main.constants import ACTIVE_STATES
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.scheduler.task_manager_models import TaskManagerModels
import awx.main.analytics.subsystem_metrics as s_metrics
from awx.main.utils import decrypt_field


logger = logging.getLogger('awx.main.scheduler')


def timeit(func):
    def inner(*args, **kwargs):
        t_now = time.perf_counter()
        result = func(*args, **kwargs)
        dur = time.perf_counter() - t_now
        args[0].subsystem_metrics.inc(f"{args[0].prefix}_{func.__name__}_seconds", dur)
        return result

    return inner


class TaskBase:
    def __init__(self, prefix=""):
        self.prefix = prefix
        # initialize each metric to 0 and force metric_has_changed to true. This
        # ensures each task manager metric will be overridden when pipe_execute
        # is called later.
        self.subsystem_metrics = s_metrics.Metrics(auto_pipe_execute=False)
        self.start_time = time.time()

        # We want to avoid calling settings in loops, so cache these settings at init time
        self.start_task_limit = settings.START_TASK_LIMIT
        self.task_manager_timeout = settings.TASK_MANAGER_TIMEOUT
        self.control_task_impact = settings.AWX_CONTROL_NODE_TASK_IMPACT

        for m in self.subsystem_metrics.METRICS:
            if m.startswith(self.prefix):
                self.subsystem_metrics.set(m, 0)

    def timed_out(self):
        """Return True/False if we have met or exceeded the timeout for the task manager."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.task_manager_timeout:
            logger.warning(f"{self.prefix} manager has run for {elapsed} which is greater than TASK_MANAGER_TIMEOUT of {settings.TASK_MANAGER_TIMEOUT}.")
            return True
        return False

    @timeit
    def get_tasks(self, filter_args):
        wf_approval_ctype_id = ContentType.objects.get_for_model(WorkflowApproval).id
        qs = (
            UnifiedJob.objects.filter(**filter_args)
            .exclude(launch_type='sync')
            .exclude(polymorphic_ctype_id=wf_approval_ctype_id)
            .order_by('created')
            .prefetch_related('dependent_jobs')
        )
        self.all_tasks = [t for t in qs]

    def record_aggregate_metrics(self, *args):
        if not is_testing():
            try:
                # increment task_manager_schedule_calls regardless if the other
                # metrics are recorded
                s_metrics.Metrics(auto_pipe_execute=True).inc(f"{self.prefix}__schedule_calls", 1)
                # Only record metrics if the last time recording was more
                # than SUBSYSTEM_METRICS_TASK_MANAGER_RECORD_INTERVAL ago.
                # Prevents a short-duration task manager that runs directly after a
                # long task manager to override useful metrics.
                current_time = time.time()
                time_last_recorded = current_time - self.subsystem_metrics.decode(f"{self.prefix}_recorded_timestamp")
                if time_last_recorded > settings.SUBSYSTEM_METRICS_TASK_MANAGER_RECORD_INTERVAL:
                    logger.debug(f"recording {self.prefix} metrics, last recorded {time_last_recorded} seconds ago")
                    self.subsystem_metrics.set(f"{self.prefix}_recorded_timestamp", current_time)
                    self.subsystem_metrics.pipe_execute()
                else:
                    logger.debug(f"skipping recording {self.prefix} metrics, last recorded {time_last_recorded} seconds ago")
            except Exception:
                logger.exception(f"Error saving metrics for {self.prefix}")

    def record_aggregate_metrics_and_exit(self, *args):
        self.record_aggregate_metrics()
        sys.exit(1)

    def get_local_metrics(self):
        data = {}
        for k, metric in self.subsystem_metrics.METRICS.items():
            if k.startswith(self.prefix) and metric.metric_has_changed:
                data[k[len(self.prefix) + 1 :]] = metric.current_value
        return data

    def schedule(self):
        # Always be able to restore the original signal handler if we finish
        original_sigusr1 = signal.getsignal(signal.SIGUSR1)

        # Lock
        with task_manager_bulk_reschedule():
            with advisory_lock(f"{self.prefix}_lock", wait=False) as acquired:
                with transaction.atomic():
                    if acquired is False:
                        logger.debug(f"Not running {self.prefix} scheduler, another task holds lock")
                        return
                    logger.debug(f"Starting {self.prefix} Scheduler")
                    # if sigusr1 due to timeout, still record metrics
                    signal.signal(signal.SIGUSR1, self.record_aggregate_metrics_and_exit)
                    try:
                        self._schedule()
                    finally:
                        # Reset the signal handler back to the default just in case anything
                        # else uses the same signal for other purposes
                        signal.signal(signal.SIGUSR1, original_sigusr1)
                    commit_start = time.time()

                    logger.debug(f"Commiting {self.prefix} Scheduler changes")

                if self.prefix == "task_manager":
                    self.subsystem_metrics.set(f"{self.prefix}_commit_seconds", time.time() - commit_start)
                local_metrics = self.get_local_metrics()
                self.record_aggregate_metrics()

                logger.debug(f"Finished {self.prefix} Scheduler, timing data:\n{local_metrics}")


class WorkflowManager(TaskBase):
    def __init__(self):
        super().__init__(prefix="workflow_manager")

    @timeit
    def spawn_workflow_graph_jobs(self):
        result = []
        for workflow_job in self.all_tasks:
            if self.timed_out():
                logger.warning("Workflow manager has reached time out while processing running workflows, exiting loop early")
                ScheduleWorkflowManager().schedule()
                # Do not process any more workflow jobs. Stop here.
                break
            dag = WorkflowDAG(workflow_job)
            status_changed = False
            if workflow_job.cancel_flag:
                workflow_job.workflow_nodes.filter(do_not_run=False, job__isnull=True).update(do_not_run=True)
                logger.debug('Canceling spawned jobs of %s due to cancel flag.', workflow_job.log_format)
                cancel_finished = dag.cancel_node_jobs()
                if cancel_finished:
                    logger.info('Marking %s as canceled, all spawned jobs have concluded.', workflow_job.log_format)
                    workflow_job.status = 'canceled'
                    workflow_job.start_args = ''  # blank field to remove encrypted passwords
                    workflow_job.save(update_fields=['status', 'start_args'])
                    status_changed = True
            else:
                dnr_nodes = dag.mark_dnr_nodes()
                WorkflowJobNode.objects.bulk_update(dnr_nodes, ['do_not_run'])
                # If workflow is now done, we do special things to mark it as done.
                is_done = dag.is_workflow_done()
                if is_done:
                    has_failed, reason = dag.has_workflow_failed()
                    logger.debug('Marking %s as %s.', workflow_job.log_format, 'failed' if has_failed else 'successful')
                    result.append(workflow_job.id)
                    new_status = 'failed' if has_failed else 'successful'
                    logger.debug("Transitioning {} to {} status.".format(workflow_job.log_format, new_status))
                    update_fields = ['status', 'start_args']
                    workflow_job.status = new_status
                    if reason:
                        logger.info(f'Workflow job {workflow_job.id} failed due to reason: {reason}')
                        workflow_job.job_explanation = gettext_noop("No error handling paths found, marking workflow as failed")
                        update_fields.append('job_explanation')
                    workflow_job.start_args = ''  # blank field to remove encrypted passwords
                    workflow_job.save(update_fields=update_fields)
                    status_changed = True

            if status_changed:
                if workflow_job.spawned_by_workflow:
                    ScheduleWorkflowManager().schedule()
                workflow_job.websocket_emit_status(workflow_job.status)
                # Operations whose queries rely on modifications made during the atomic scheduling session
                workflow_job.send_notification_templates('succeeded' if workflow_job.status == 'successful' else 'failed')

            if workflow_job.status == 'running':
                spawn_nodes = dag.bfs_nodes_to_run()
                if spawn_nodes:
                    logger.debug('Spawning jobs for %s', workflow_job.log_format)
                else:
                    logger.debug('No nodes to spawn for %s', workflow_job.log_format)
                for spawn_node in spawn_nodes:
                    if spawn_node.unified_job_template is None:
                        continue
                    kv = spawn_node.get_job_kwargs()
                    job = spawn_node.unified_job_template.create_unified_job(**kv)
                    spawn_node.job = job
                    spawn_node.save()
                    logger.debug('Spawned %s in %s for node %s', job.log_format, workflow_job.log_format, spawn_node.pk)
                    can_start = True
                    if isinstance(spawn_node.unified_job_template, WorkflowJobTemplate):
                        workflow_ancestors = job.get_ancestor_workflows()
                        if spawn_node.unified_job_template in set(workflow_ancestors):
                            can_start = False
                            logger.info(
                                'Refusing to start recursive workflow-in-workflow id={}, wfjt={}, ancestors={}'.format(
                                    job.id, spawn_node.unified_job_template.pk, [wa.pk for wa in workflow_ancestors]
                                )
                            )
                            display_list = [spawn_node.unified_job_template] + workflow_ancestors
                            job.job_explanation = gettext_noop(
                                "Workflow Job spawned from workflow could not start because it "
                                "would result in recursion (spawn order, most recent first: {})"
                            ).format(', '.join('<{}>'.format(tmp) for tmp in display_list))
                        else:
                            logger.debug(
                                'Starting workflow-in-workflow id={}, wfjt={}, ancestors={}'.format(
                                    job.id, spawn_node.unified_job_template.pk, [wa.pk for wa in workflow_ancestors]
                                )
                            )
                    if not job._resources_sufficient_for_launch():
                        can_start = False
                        job.job_explanation = gettext_noop(
                            "Job spawned from workflow could not start because it was missing a related resource such as project or inventory"
                        )
                    if can_start:
                        if workflow_job.start_args:
                            start_args = json.loads(decrypt_field(workflow_job, 'start_args'))
                        else:
                            start_args = {}
                        can_start = job.signal_start(**start_args)
                        if not can_start:
                            job.job_explanation = gettext_noop(
                                "Job spawned from workflow could not start because it was not in the right state or required manual credentials"
                            )
                    if not can_start:
                        job.status = 'failed'
                        job.save(update_fields=['status', 'job_explanation'])
                        job.websocket_emit_status('failed')
                        # NOTE: sending notification templates here is slightly worse performance
                        # this is not yet optimized in the same way as for the TaskManager
                        job.send_notification_templates('failed')
                        ScheduleWorkflowManager().schedule()

                    # TODO: should we emit a status on the socket here similar to tasks.py awx_periodic_scheduler() ?
                    # emit_websocket_notification('/socket.io/jobs', '', dict(id=))

        return result

    @timeit
    def get_tasks(self, filter_args):
        self.all_tasks = [wf for wf in WorkflowJob.objects.filter(**filter_args)]

    @timeit
    def _schedule(self):
        self.get_tasks(dict(status__in=["running"], dependencies_processed=True))
        if len(self.all_tasks) > 0:
            self.spawn_workflow_graph_jobs()


class DependencyManager(TaskBase):
    def __init__(self):
        super().__init__(prefix="dependency_manager")
        self.all_projects = {}
        self.all_inventory_sources = {}

    def cache_projects_and_sources(self, task_list):
        project_ids = set()
        inventory_ids = set()
        for task in task_list:
            if isinstance(task, Job):
                if task.project_id:
                    project_ids.add(task.project_id)
                if task.inventory_id:
                    inventory_ids.add(task.inventory_id)
            elif isinstance(task, InventoryUpdate):
                if task.inventory_source and task.inventory_source.source_project_id:
                    project_ids.add(task.inventory_source.source_project_id)

        for proj in Project.objects.filter(id__in=project_ids, scm_update_on_launch=True):
            self.all_projects[proj.id] = proj

        for invsrc in InventorySource.objects.filter(inventory_id__in=inventory_ids, update_on_launch=True):
            self.all_inventory_sources.setdefault(invsrc.inventory_id, [])
            self.all_inventory_sources[invsrc.inventory_id].append(invsrc)

    @staticmethod
    def should_update_again(update, cache_timeout):
        '''
        If it has never updated, we need to update
        If there is already an update in progress then we do not need to a new create one
        If the last update failed, we always need to try and update again
        If current time is more than cache_timeout after last update, then we need a new one
        '''
        if (update is None) or (update.status in ['failed', 'canceled', 'error']):
            return True
        if update.status in ['waiting', 'pending', 'running']:
            return False

        return bool(((update.finished + timedelta(seconds=cache_timeout))) < tz_now())

    def get_or_create_project_update(self, project_id):
        project = self.all_projects.get(project_id, None)
        if project is not None:
            latest_project_update = project.project_updates.filter(job_type='check').order_by("-created").first()
            if self.should_update_again(latest_project_update, project.scm_update_cache_timeout):
                project_task = project.create_project_update(_eager_fields=dict(launch_type='dependency'))
                project_task.signal_start()
                return [project_task]
            else:
                return [latest_project_update]
        return []

    def gen_dep_for_job(self, task):
        dependencies = self.get_or_create_project_update(task.project_id)

        try:
            start_args = json.loads(decrypt_field(task, field_name="start_args"))
        except ValueError:
            start_args = dict()
        # generator for update-on-launch inventory sources related to this task
        for inventory_source in self.all_inventory_sources.get(task.inventory_id, []):
            if "inventory_sources_already_updated" in start_args and inventory_source.id in start_args['inventory_sources_already_updated']:
                continue
            latest_inventory_update = inventory_source.inventory_updates.order_by("-created").first()
            if self.should_update_again(latest_inventory_update, inventory_source.update_cache_timeout):
                inventory_task = inventory_source.create_inventory_update(_eager_fields=dict(launch_type='dependency'))
                inventory_task.signal_start()
                dependencies.append(inventory_task)
            else:
                dependencies.append(latest_inventory_update)

        return dependencies

    def gen_dep_for_inventory_update(self, inventory_task):
        if inventory_task.source == "scm":
            invsrc = inventory_task.inventory_source
            if invsrc:
                return self.get_or_create_project_update(invsrc.source_project_id)
        return []

    @timeit
    def generate_dependencies(self, undeped_tasks):
        dependencies = []
        self.cache_projects_and_sources(undeped_tasks)
        for task in undeped_tasks:
            task.log_lifecycle("acknowledged")
            if type(task) is Job:
                job_deps = self.gen_dep_for_job(task)
            elif type(task) is InventoryUpdate:
                job_deps = self.gen_dep_for_inventory_update(task)
            else:
                continue
            if job_deps:
                dependencies += job_deps
                with disable_activity_stream():
                    task.dependent_jobs.add(*dependencies)
                logger.debug(f'Linked {[dep.log_format for dep in dependencies]} as dependencies of {task.log_format}')

        UnifiedJob.objects.filter(pk__in=[task.pk for task in undeped_tasks]).update(dependencies_processed=True)

        return dependencies

    @timeit
    def _schedule(self):
        self.get_tasks(dict(status__in=["pending"], dependencies_processed=False))

        if len(self.all_tasks) > 0:
            deps = self.generate_dependencies(self.all_tasks)
            undeped_deps = [dep for dep in deps if dep.dependencies_processed is False]
            self.generate_dependencies(undeped_deps)
            self.subsystem_metrics.inc(f"{self.prefix}_pending_processed", len(self.all_tasks) + len(undeped_deps))
            ScheduleTaskManager().schedule()


class TaskManager(TaskBase):
    def __init__(self):
        """
        Do NOT put database queries or other potentially expensive operations
        in the task manager init. The task manager object is created every time a
        job is created, transitions state, and every 30 seconds on each tower node.
        More often then not, the object is destroyed quickly because the NOOP case is hit.

        The NOOP case is short-circuit logic. If the task manager realizes that another instance
        of the task manager is already running, then it short-circuits and decides not to run.
        """
        # start task limit indicates how many pending jobs can be started on this
        # .schedule() run. Starting jobs is expensive, and there is code in place to reap
        # the task manager after 5 minutes. At scale, the task manager can easily take more than
        # 5 minutes to start pending jobs. If this limit is reached, pending jobs
        # will no longer be started and will be started on the next task manager cycle.
        self.time_delta_job_explanation = timedelta(seconds=30)
        super().__init__(prefix="task_manager")

    def after_lock_init(self):
        """
        Init AFTER we know this instance of the task manager will run because the lock is acquired.
        """
        self.dependency_graph = DependencyGraph()
        self.tm_models = TaskManagerModels()
        self.controlplane_ig = self.tm_models.instance_groups.controlplane_ig

    def process_job_dep_failures(self, task):
        """If job depends on a job that has failed, mark as failed and handle misc stuff."""
        for dep in task.dependent_jobs.all():
            # if we detect a failed or error dependency, go ahead and fail this task.
            if dep.status in ("error", "failed"):
                task.status = 'failed'
                logger.warning(f'Previous task failed task: {task.id} dep: {dep.id} task manager')
                task.job_explanation = 'Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % (
                    get_type_for_model(type(dep)),
                    dep.name,
                    dep.id,
                )
                task.save(update_fields=['status', 'job_explanation'])
                task.websocket_emit_status('failed')
                self.pre_start_failed.append(task.id)
                return True

        return False

    def job_blocked_by(self, task):
        # TODO: I'm not happy with this, I think blocking behavior should be decided outside of the dependency graph
        #       in the old task manager this was handled as a method on each task object outside of the graph and
        #       probably has the side effect of cutting down *a lot* of the logic from this task manager class
        blocked_by = self.dependency_graph.task_blocked_by(task)
        if blocked_by:
            return blocked_by

        for dep in task.dependent_jobs.all():
            if dep.status in ACTIVE_STATES:
                return dep

        return None

    @timeit
    def start_task(self, task, instance_group, instance=None):
        # Just like for process_running_tasks, add the job to the dependency graph and
        # ask the TaskManagerInstanceGroups object to update consumed capacity on all
        # implicated instances and container groups.
        self.dependency_graph.add_job(task)
        if instance_group is not None:
            task.instance_group = instance_group
        # We need the instance group assigned to correctly account for container group max_concurrent_jobs and max_forks
        self.tm_models.consume_capacity(task)

        self.subsystem_metrics.inc(f"{self.prefix}_tasks_started", 1)
        self.start_task_limit -= 1
        if self.start_task_limit == 0:
            # schedule another run immediately after this task manager
            ScheduleTaskManager().schedule()

        task.status = 'waiting'

        (start_status, opts) = task.pre_start()
        if not start_status:
            task.status = 'failed'
            if task.job_explanation:
                task.job_explanation += ' '
            task.job_explanation += 'Task failed pre-start check.'
            task.save()
            self.pre_start_failed.append(task.id)
        else:
            if type(task) is WorkflowJob:
                task.status = 'running'
                task.send_notification_templates('running')
                logger.debug('Transitioning %s to running status.', task.log_format)
                # Call this to ensure Workflow nodes get spawned in timely manner
                ScheduleWorkflowManager().schedule()
            # at this point we already have control/execution nodes selected for the following cases
            else:
                execution_node_msg = f' and execution node {task.execution_node}' if task.execution_node else ''
                logger.debug(
                    f'Submitting job {task.log_format} controlled by {task.controller_node} to instance group {instance_group.name}{execution_node_msg}.'
                )
            with disable_activity_stream():
                task.celery_task_id = str(uuid.uuid4())
                task.save()
                task.log_lifecycle("waiting")

        # apply_async does a NOTIFY to the channel dispatcher is listening to
        # postgres will treat this as part of the transaction, which is what we want
        if task.status != 'failed' and type(task) is not WorkflowJob:
            task_cls = task._get_task_class()
            task_cls.apply_async(
                [task.pk],
                opts,
                queue=task.get_queue_name(),
                uuid=task.celery_task_id,
            )

        # In exception cases, like a job failing pre-start checks, we send the websocket status message.
        # For jobs going into waiting, we omit this because of performance issues, as it should go to running quickly
        if task.status != 'waiting':
            task.websocket_emit_status(task.status)  # adds to on_commit

    @timeit
    def process_running_tasks(self, running_tasks):
        for task in running_tasks:
            if type(task) is WorkflowJob:
                ScheduleWorkflowManager().schedule()
            self.dependency_graph.add_job(task)
            self.tm_models.consume_capacity(task)

    @timeit
    def process_pending_tasks(self, pending_tasks):
        tasks_to_update_job_explanation = []
        for task in pending_tasks:
            if self.start_task_limit <= 0:
                break
            if self.timed_out():
                logger.warning("Task manager has reached time out while processing pending jobs, exiting loop early")
                break

            has_failed = self.process_job_dep_failures(task)
            if has_failed:
                continue

            blocked_by = self.job_blocked_by(task)
            if blocked_by:
                self.subsystem_metrics.inc(f"{self.prefix}_tasks_blocked", 1)
                task.log_lifecycle("blocked", blocked_by=blocked_by)
                job_explanation = gettext_noop(f"waiting for {blocked_by._meta.model_name}-{blocked_by.id} to finish")
                if task.job_explanation != job_explanation:
                    if task.created < (tz_now() - self.time_delta_job_explanation):
                        task.job_explanation = job_explanation
                        tasks_to_update_job_explanation.append(task)
                continue

            if isinstance(task, WorkflowJob):
                # Previously we were tracking allow_simultaneous blocking both here and in DependencyGraph.
                # Double check that using just the DependencyGraph works for Workflows and Sliced Jobs.
                self.start_task(task, None, None)
                continue

            found_acceptable_queue = False

            # Determine if there is control capacity for the task
            if task.capacity_type == 'control':
                control_impact = task.task_impact + self.control_task_impact
            else:
                control_impact = self.control_task_impact
            control_instance = self.tm_models.instance_groups.fit_task_to_most_remaining_capacity_instance(
                task, instance_group_name=self.controlplane_ig.name, impact=control_impact, capacity_type='control'
            )
            if not control_instance:
                self.task_needs_capacity(task, tasks_to_update_job_explanation)
                logger.debug(f"Skipping task {task.log_format} in pending, not enough capacity left on controlplane to control new tasks")
                continue

            task.controller_node = control_instance.hostname

            # All task.capacity_type == 'control' jobs should run on control plane, no need to loop over instance groups
            if task.capacity_type == 'control':
                if not self.tm_models.instance_groups[self.controlplane_ig.name].has_remaining_capacity(control_impact=True):
                    continue
                task.execution_node = control_instance.hostname
                execution_instance = self.tm_models.instances[control_instance.hostname].obj
                task.log_lifecycle("controller_node_chosen")
                task.log_lifecycle("execution_node_chosen")
                self.start_task(task, self.controlplane_ig, execution_instance)
                found_acceptable_queue = True
                continue

            for instance_group in self.tm_models.instance_groups.get_instance_groups_from_task_cache(task):
                if not self.tm_models.instance_groups[instance_group.name].has_remaining_capacity(task):
                    continue
                if instance_group.is_container_group:
                    self.start_task(task, instance_group, None)
                    found_acceptable_queue = True
                    break

                # at this point we know the instance group is NOT a container group
                # because if it was, it would have started the task and broke out of the loop.
                execution_instance = self.tm_models.instance_groups.fit_task_to_most_remaining_capacity_instance(
                    task, instance_group_name=instance_group.name, add_hybrid_control_cost=True
                ) or self.tm_models.instance_groups.find_largest_idle_instance(instance_group_name=instance_group.name, capacity_type=task.capacity_type)

                if execution_instance:
                    task.execution_node = execution_instance.hostname
                    # If our execution instance is a hybrid, prefer to do control tasks there as well.
                    if execution_instance.node_type == 'hybrid':
                        control_instance = execution_instance
                        task.controller_node = execution_instance.hostname

                    task.log_lifecycle("controller_node_chosen")
                    task.log_lifecycle("execution_node_chosen")
                    logger.debug(
                        "Starting {} in group {} instance {} (remaining_capacity={})".format(
                            task.log_format, instance_group.name, execution_instance.hostname, execution_instance.remaining_capacity
                        )
                    )
                    execution_instance = self.tm_models.instances[execution_instance.hostname].obj
                    self.start_task(task, instance_group, execution_instance)
                    found_acceptable_queue = True
                    break
                else:
                    logger.debug(
                        "No instance available in group {} to run job {} w/ capacity requirement {}".format(
                            instance_group.name, task.log_format, task.task_impact
                        )
                    )
            if not found_acceptable_queue:
                self.task_needs_capacity(task, tasks_to_update_job_explanation)
        UnifiedJob.objects.bulk_update(tasks_to_update_job_explanation, ['job_explanation'])

    def task_needs_capacity(self, task, tasks_to_update_job_explanation):
        task.log_lifecycle("needs_capacity")
        job_explanation = gettext_noop("This job is not ready to start because there is not enough available capacity.")
        if task.job_explanation != job_explanation:
            if task.created < (tz_now() - self.time_delta_job_explanation):
                # Many launched jobs are immediately blocked, but most blocks will resolve in a few seconds.
                # Therefore we should only update the job_explanation after some time has elapsed to
                # prevent excessive task saves.
                task.job_explanation = job_explanation
                tasks_to_update_job_explanation.append(task)
        logger.debug("{} couldn't be scheduled on graph, waiting for next cycle".format(task.log_format))

    def reap_jobs_from_orphaned_instances(self):
        # discover jobs that are in running state but aren't on an execution node
        # that we know about; this is a fairly rare event, but it can occur if you,
        # for example, SQL backup an awx install with running jobs and restore it
        # elsewhere
        for j in UnifiedJob.objects.filter(
            status__in=['pending', 'waiting', 'running'],
        ).exclude(execution_node__in=Instance.objects.exclude(node_type='hop').values_list('hostname', flat=True)):
            if j.execution_node and not j.is_container_group_task:
                logger.error(f'{j.execution_node} is not a registered instance; reaping {j.log_format}')
                reap_job(j, 'failed')

    def process_tasks(self):
        # maintain a list of jobs that went to an early failure state,
        # meaning the dispatcher never got these jobs,
        # that means we have to handle notifications for those
        self.pre_start_failed = []

        running_tasks = [t for t in self.all_tasks if t.status in ['waiting', 'running']]
        self.process_running_tasks(running_tasks)
        self.subsystem_metrics.inc(f"{self.prefix}_running_processed", len(running_tasks))

        pending_tasks = [t for t in self.all_tasks if t.status == 'pending']

        self.process_pending_tasks(pending_tasks)
        self.subsystem_metrics.inc(f"{self.prefix}_pending_processed", len(pending_tasks))

        if self.pre_start_failed:
            from awx.main.tasks.system import handle_failure_notifications

            handle_failure_notifications.delay(self.pre_start_failed)

    def timeout_approval_node(self, task):
        if self.timed_out():
            logger.warning("Task manager has reached time out while processing approval nodes, exiting loop early")
            # Do not process any more workflow approval nodes. Stop here.
            # Maybe we should schedule another TaskManager run
            return
        timeout_message = _("The approval node {name} ({pk}) has expired after {timeout} seconds.").format(name=task.name, pk=task.pk, timeout=task.timeout)
        logger.warning(timeout_message)
        task.timed_out = True
        task.status = 'failed'
        task.send_approval_notification('timed_out')
        task.websocket_emit_status(task.status)
        task.job_explanation = timeout_message
        task.save(update_fields=['status', 'job_explanation', 'timed_out'])

    def get_expired_workflow_approvals(self):
        # timeout of 0 indicates that it never expires
        qs = WorkflowApproval.objects.filter(status='pending').exclude(timeout=0).filter(expires__lt=tz_now())
        return qs

    @timeit
    def _schedule(self):
        self.get_tasks(dict(status__in=["pending", "waiting", "running"], dependencies_processed=True))

        self.after_lock_init()
        self.reap_jobs_from_orphaned_instances()

        if len(self.all_tasks) > 0:
            self.process_tasks()

        for workflow_approval in self.get_expired_workflow_approvals():
            self.timeout_approval_node(workflow_approval)
