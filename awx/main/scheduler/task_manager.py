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
from django.db import transaction, connection
from django.utils.translation import gettext_lazy as _, gettext_noop
from django.utils.timezone import now as tz_now
from django.conf import settings

# AWX
from awx.main.dispatch.reaper import reap_job
from awx.main.models import (
    AdHocCommand,
    Instance,
    InventorySource,
    InventoryUpdate,
    Job,
    Project,
    ProjectUpdate,
    SystemJob,
    UnifiedJob,
    WorkflowApproval,
    WorkflowJob,
    WorkflowJobNode,
    WorkflowJobTemplate,
)
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.main.utils.pglock import advisory_lock
from awx.main.utils import get_type_for_model, task_manager_bulk_reschedule, schedule_task_manager
from awx.main.utils.common import create_partition
from awx.main.signals import disable_activity_stream
from awx.main.constants import ACTIVE_STATES
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.scheduler.task_manager_models import TaskManagerInstances
from awx.main.scheduler.task_manager_models import TaskManagerInstanceGroups
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
    def __init__(self):
        # initialize each metric to 0 and force metric_has_changed to true. This
        # ensures each task manager metric will be overridden when pipe_execute
        # is called later.
        self.subsystem_metrics = s_metrics.Metrics(auto_pipe_execute=False)
        for m in self.subsystem_metrics.METRICS:
            if m.startswith(self.prefix):
                self.subsystem_metrics.set(m, 0)

    def get_running_workflow_jobs(self):
        graph_workflow_jobs = [wf for wf in WorkflowJob.objects.filter(status='running')]
        return graph_workflow_jobs

    @timeit
    def get_tasks(self, filter_args):
        qs = UnifiedJob.objects.filter(**filter_args).exclude(launch_type='sync').order_by('created').prefetch_related('instance_group')
        return [task for task in qs if not type(task) is WorkflowJob]

    def record_aggregate_metrics(self, *args):
        if not settings.IS_TESTING():
            # increment task_manager_schedule_calls regardless if the other
            # metrics are recorded
            s_metrics.Metrics(auto_pipe_execute=True).inc(f"{self.prefix}_schedule_calls", 1)
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

    def record_aggregate_metrics_and_exit(self, *args):
        self.record_aggregate_metrics()
        sys.exit(1)

    def schedule(self):
        # Lock
        with advisory_lock(f"{self.prefix}_lock", wait=False) as acquired:
            with transaction.atomic():
                if acquired is False:
                    logger.debug(f"Not running {self.prefix} scheduler, another task holds lock")
                    return
                logger.debug(f"Starting {self.prefix} Scheduler")
                with task_manager_bulk_reschedule():
                    # if sigterm due to timeout, still record metrics
                    signal.signal(signal.SIGTERM, self.record_aggregate_metrics_and_exit)
                    self._schedule()
                    self.record_aggregate_metrics()
                logger.debug(f"Finishing {self.prefix} Scheduler")


class WorkflowManager(TaskBase):
    def __init__(self):
        self.prefix = "workflow_manager"
        super().__init__()

    @timeit
    def spawn_workflow_graph_jobs(self, workflow_jobs):
        result = []
        for workflow_job in workflow_jobs:
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
                workflow_nodes = dag.mark_dnr_nodes()
                WorkflowJobNode.objects.bulk_update(workflow_nodes, ['do_not_run'])
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
                    schedule_task_manager()
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
                            ).format(', '.join(['<{}>'.format(tmp) for tmp in display_list]))
                        else:
                            logger.debug(
                                'Starting workflow-in-workflow id={}, wfjt={}, ancestors={}'.format(
                                    job.id, spawn_node.unified_job_template.pk, [wa.pk for wa in workflow_ancestors]
                                )
                            )
                    if not job._resources_sufficient_for_launch():
                        can_start = False
                        job.job_explanation = gettext_noop(
                            "Job spawned from workflow could not start because it " "was missing a related resource such as project or inventory"
                        )
                    if can_start:
                        if workflow_job.start_args:
                            start_args = json.loads(decrypt_field(workflow_job, 'start_args'))
                        else:
                            start_args = {}
                        can_start = job.signal_start(**start_args)
                        if not can_start:
                            job.job_explanation = gettext_noop(
                                "Job spawned from workflow could not start because it " "was not in the right state or required manual credentials"
                            )
                    if not can_start:
                        job.status = 'failed'
                        job.save(update_fields=['status', 'job_explanation'])
                        job.websocket_emit_status('failed')

                    # TODO: should we emit a status on the socket here similar to tasks.py awx_periodic_scheduler() ?
                    # emit_websocket_notification('/socket.io/jobs', '', dict(id=))

        return result

    def timeout_approval_node(self):
        workflow_approvals = WorkflowApproval.objects.filter(status='pending')
        now = tz_now()
        for task in workflow_approvals:
            approval_timeout_seconds = timedelta(seconds=task.timeout)
            if task.timeout == 0:
                continue
            if (now - task.created) >= approval_timeout_seconds:
                timeout_message = _("The approval node {name} ({pk}) has expired after {timeout} seconds.").format(
                    name=task.name, pk=task.pk, timeout=task.timeout
                )
                logger.warning(timeout_message)
                task.timed_out = True
                task.status = 'failed'
                task.send_approval_notification('timed_out')
                task.websocket_emit_status(task.status)
                task.job_explanation = timeout_message
                task.save(update_fields=['status', 'job_explanation', 'timed_out'])

    @timeit
    def get_tasks(self):
        workflow_jobs_running = [wf for wf in WorkflowJob.objects.filter(status='running')]
        workflow_jobs_pending = [wf for wf in WorkflowJob.objects.filter(status='pending')]
        workflow_to_start = []
        running_workflow_pk = {wf.pk for wf in workflow_jobs_running}
        for wf in workflow_jobs_pending:
            if wf.allow_simultaneous or wf.pk not in running_workflow_pk:
                wf.status = 'running'
                workflow_to_start.append(wf)

        WorkflowJob.objects.bulk_update(workflow_to_start, ['status'])
        workflow_jobs_running.extend(workflow_to_start)
        return workflow_jobs_running

    @timeit
    def _schedule(self):
        running_workflow_tasks = self.get_tasks()
        if len(running_workflow_tasks) > 0:
            self.spawn_workflow_graph_jobs(running_workflow_tasks)
            self.timeout_approval_node()


class DependencyManager(TaskBase):
    def __init__(self):
        self.prefix = "dependency_manager"
        super().__init__()

    def create_project_update(self, task, project_id=None):
        if project_id is None:
            project_id = task.project_id
        project_task = Project.objects.get(id=project_id).create_project_update(_eager_fields=dict(launch_type='dependency'))

        # Project created 1 seconds behind
        project_task.created = task.created - timedelta(seconds=1)
        project_task.status = 'pending'
        project_task.save()
        logger.debug('Spawned {} as dependency of {}'.format(project_task.log_format, task.log_format))
        return project_task

    def create_inventory_update(self, task, inventory_source_task):
        inventory_task = InventorySource.objects.get(id=inventory_source_task.id).create_inventory_update(_eager_fields=dict(launch_type='dependency'))

        inventory_task.created = task.created - timedelta(seconds=2)
        inventory_task.status = 'pending'
        inventory_task.save()
        logger.debug('Spawned {} as dependency of {}'.format(inventory_task.log_format, task.log_format))

        return inventory_task

    def add_dependencies(self, task, dependencies):
        with disable_activity_stream():
            task.dependent_jobs.add(*dependencies)

    def get_inventory_source_tasks(self, all_sorted_tasks):
        inventory_ids = set()
        for task in all_sorted_tasks:
            if isinstance(task, Job):
                inventory_ids.add(task.inventory_id)
        return [invsrc for invsrc in InventorySource.objects.filter(inventory_id__in=inventory_ids, update_on_launch=True)]

    def get_latest_inventory_update(self, inventory_source):
        latest_inventory_update = InventoryUpdate.objects.filter(inventory_source=inventory_source).order_by("-created")
        if not latest_inventory_update.exists():
            return None
        return latest_inventory_update.first()

    def should_update_inventory_source(self, job, latest_inventory_update):
        now = tz_now()

        if latest_inventory_update is None:
            return True
        '''
        If there's already a inventory update utilizing this job that's about to run
        then we don't need to create one
        '''
        if latest_inventory_update.status in ['waiting', 'pending', 'running']:
            return False

        timeout_seconds = timedelta(seconds=latest_inventory_update.inventory_source.update_cache_timeout)
        if (latest_inventory_update.finished + timeout_seconds) < now:
            return True
        if latest_inventory_update.inventory_source.update_on_launch is True and latest_inventory_update.status in ['failed', 'canceled', 'error']:
            return True
        return False

    def get_latest_project_update(self, project_id):
        latest_project_update = ProjectUpdate.objects.filter(project=project_id, job_type='check').order_by("-created")
        if not latest_project_update.exists():
            return None
        return latest_project_update.first()

    def should_update_related_project(self, job, latest_project_update):
        now = tz_now()

        if latest_project_update is None:
            return True

        if latest_project_update.status in ['failed', 'canceled']:
            return True

        '''
        If there's already a project update utilizing this job that's about to run
        then we don't need to create one
        '''
        if latest_project_update.status in ['waiting', 'pending', 'running']:
            return False

        '''
        If the latest project update has a created time == job_created_time-1
        then consider the project update found. This is so we don't enter an infinite loop
        of updating the project when cache timeout is 0.
        '''
        if (
            latest_project_update.project.scm_update_cache_timeout == 0
            and latest_project_update.launch_type == 'dependency'
            and latest_project_update.created == job.created - timedelta(seconds=1)
        ):
            return False
        '''
        Normal Cache Timeout Logic
        '''
        timeout_seconds = timedelta(seconds=latest_project_update.project.scm_update_cache_timeout)
        if (latest_project_update.finished + timeout_seconds) < now:
            return True
        return False

    def gen_dep_for_job(self, task):
        created_dependencies = []
        dependencies = []
        # TODO: Can remove task.project None check after scan-job-default-playbook is removed
        if task.project is not None and task.project.scm_update_on_launch is True:
            latest_project_update = self.get_latest_project_update(task.project_id)
            if self.should_update_related_project(task, latest_project_update):
                latest_project_update = self.create_project_update(task)
                created_dependencies.append(latest_project_update)
            dependencies.append(latest_project_update)

        # Inventory created 2 seconds behind job
        try:
            start_args = json.loads(decrypt_field(task, field_name="start_args"))
        except ValueError:
            start_args = dict()
        # generator for inventory sources related to this task
        task_inv_sources = (invsrc for invsrc in self.all_inventory_sources if invsrc.inventory_id == task.inventory_id)
        for inventory_source in task_inv_sources:
            if "inventory_sources_already_updated" in start_args and inventory_source.id in start_args['inventory_sources_already_updated']:
                continue
            if not inventory_source.update_on_launch:
                continue
            latest_inventory_update = self.get_latest_inventory_update(inventory_source)
            if self.should_update_inventory_source(task, latest_inventory_update):
                inventory_task = self.create_inventory_update(task, inventory_source)
                created_dependencies.append(inventory_task)
                dependencies.append(inventory_task)
            else:
                dependencies.append(latest_inventory_update)

        if dependencies:
            self.add_dependencies(task, dependencies)

        return created_dependencies

    def gen_dep_for_inventory_update(self, inventory_task):
        created_dependencies = []
        if inventory_task.source == "scm":
            invsrc = inventory_task.inventory_source
            if not invsrc.source_project.scm_update_on_launch:
                return created_dependencies

            latest_src_project_update = self.get_latest_project_update(invsrc.source_project_id)
            if self.should_update_related_project(inventory_task, latest_src_project_update):
                latest_src_project_update = self.create_project_update(inventory_task, project_id=invsrc.source_project_id)
                created_dependencies.append(latest_src_project_update)
            self.add_dependencies(inventory_task, [latest_src_project_update])
            latest_src_project_update.scm_inventory_updates.add(inventory_task)
        return created_dependencies

    @timeit
    def generate_dependencies(self, undeped_tasks):
        created_dependencies = []
        for task in undeped_tasks:
            task.log_lifecycle("acknowledged")
            if type(task) is Job:
                created_dependencies += self.gen_dep_for_job(task)
            elif type(task) is InventoryUpdate:
                created_dependencies += self.gen_dep_for_inventory_update(task)
            else:
                continue
        UnifiedJob.objects.filter(pk__in=[task.pk for task in undeped_tasks]).update(dependencies_processed=True)

        return created_dependencies

    def process_tasks(self, all_sorted_tasks):
        self.generate_dependencies(all_sorted_tasks)
        self.subsystem_metrics.inc(f"{self.prefix}_pending_processed", len(all_sorted_tasks))

    @timeit
    def _schedule(self):
        all_sorted_tasks = self.get_tasks(dict(status__in=["pending"], dependencies_processed=False))

        if len(all_sorted_tasks) > 0:
            self.all_inventory_sources = self.get_inventory_source_tasks(all_sorted_tasks)
            self.process_tasks(all_sorted_tasks)
            schedule_task_manager()


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
        self.start_task_limit = settings.START_TASK_LIMIT
        self.time_delta_job_explanation = timedelta(seconds=30)
        self.prefix = "task_manager"
        super().__init__()

    def after_lock_init(self, all_sorted_tasks):
        """
        Init AFTER we know this instance of the task manager will run because the lock is acquired.
        """
        self.dependency_graph = DependencyGraph()
        self.instances = TaskManagerInstances(all_sorted_tasks)
        self.instance_groups = TaskManagerInstanceGroups(instances_by_hostname=self.instances)
        self.controlplane_ig = self.instance_groups.controlplane_ig

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
            # if we detect a failed or error dependency, go ahead and fail this
            # task. The errback on the dependency takes some time to trigger,
            # and we don't want the task to enter running state if its
            # dependency has failed or errored.
            elif dep.status in ("error", "failed"):
                task.status = 'failed'
                task.job_explanation = 'Previous Task Failed: {"job_type": "%s", "job_name": "%s", "job_id": "%s"}' % (
                    get_type_for_model(type(dep)),
                    dep.name,
                    dep.id,
                )
                task.save(update_fields=['status', 'job_explanation'])
                task.websocket_emit_status('failed')
                return dep

        return None

    @timeit
    def start_task(self, task, instance_group, dependent_tasks=None, instance=None):
        self.subsystem_metrics.inc(f"{self.prefix}_tasks_started", 1)
        self.start_task_limit -= 1
        if self.start_task_limit == 0:
            # schedule another run immediately after this task manager
            schedule_task_manager()
        from awx.main.tasks.system import handle_work_error, handle_work_success

        dependent_tasks = dependent_tasks or []

        task_actual = {
            'type': get_type_for_model(type(task)),
            'id': task.id,
        }
        dependencies = [{'type': get_type_for_model(type(t)), 'id': t.id} for t in dependent_tasks]

        task.status = 'waiting'

        (start_status, opts) = task.pre_start()
        if not start_status:
            task.status = 'failed'
            if task.job_explanation:
                task.job_explanation += ' '
            task.job_explanation += 'Task failed pre-start check.'
            task.save()
            # TODO: run error handler to fail sub-tasks and send notifications
        else:
            # at this point we already have control/execution nodes selected for the following cases
            task.instance_group = instance_group
            execution_node_msg = f' and execution node {task.execution_node}' if task.execution_node else ''
            logger.debug(f'Submitting job {task.log_format} controlled by {task.controller_node} to instance group {instance_group.name}{execution_node_msg}.')
            with disable_activity_stream():
                task.celery_task_id = str(uuid.uuid4())
                task.save()
                task.log_lifecycle("waiting")

        def post_commit():
            if task.status != 'failed' and type(task) is not WorkflowJob:
                # Before task is dispatched, ensure that job_event partitions exist
                create_partition(task.event_class._meta.db_table, start=task.created)
                task_cls = task._get_task_class()
                task_cls.apply_async(
                    [task.pk],
                    opts,
                    queue=task.get_queue_name(),
                    uuid=task.celery_task_id,
                    callbacks=[{'task': handle_work_success.name, 'kwargs': {'task_actual': task_actual}}],
                    errbacks=[{'task': handle_work_error.name, 'args': [task.celery_task_id], 'kwargs': {'subtasks': [task_actual] + dependencies}}],
                )

        task.websocket_emit_status(task.status)  # adds to on_commit
        connection.on_commit(post_commit)

    @timeit
    def process_running_tasks(self, running_tasks):
        for task in running_tasks:
            self.dependency_graph.add_job(task)

    @timeit
    def process_pending_tasks(self, pending_tasks):
        tasks_to_update_job_explanation = []
        for task in pending_tasks:
            if self.start_task_limit <= 0:
                break
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

            found_acceptable_queue = False
            preferred_instance_groups = task.preferred_instance_groups

            # Determine if there is control capacity for the task
            if task.capacity_type == 'control':
                control_impact = task.task_impact + settings.AWX_CONTROL_NODE_TASK_IMPACT
            else:
                control_impact = settings.AWX_CONTROL_NODE_TASK_IMPACT
            control_instance = self.instance_groups.fit_task_to_most_remaining_capacity_instance(
                task, instance_group_name=settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME, impact=control_impact, capacity_type='control'
            )
            if not control_instance:
                self.task_needs_capacity(task, tasks_to_update_job_explanation)
                logger.debug(f"Skipping task {task.log_format} in pending, not enough capacity left on controlplane to control new tasks")
                continue

            task.controller_node = control_instance.hostname

            # All task.capacity_type == 'control' jobs should run on control plane, no need to loop over instance groups
            if task.capacity_type == 'control':
                task.execution_node = control_instance.hostname
                control_instance.consume_capacity(control_impact)
                self.dependency_graph.add_job(task)
                execution_instance = self.instances[control_instance.hostname].obj
                task.log_lifecycle("controller_node_chosen")
                task.log_lifecycle("execution_node_chosen")
                self.start_task(task, self.controlplane_ig, task.get_jobs_fail_chain(), execution_instance)
                found_acceptable_queue = True
                continue

            for instance_group in preferred_instance_groups:
                if instance_group.is_container_group:
                    self.dependency_graph.add_job(task)
                    self.start_task(task, instance_group, task.get_jobs_fail_chain(), None)
                    found_acceptable_queue = True
                    break

                # TODO: remove this after we have confidence that OCP control nodes are reporting node_type=control
                if settings.IS_K8S and task.capacity_type == 'execution':
                    logger.debug("Skipping group {}, task cannot run on control plane".format(instance_group.name))
                    continue
                # at this point we know the instance group is NOT a container group
                # because if it was, it would have started the task and broke out of the loop.
                execution_instance = self.instance_groups.fit_task_to_most_remaining_capacity_instance(
                    task, instance_group_name=instance_group.name, add_hybrid_control_cost=True
                ) or self.instance_groups.find_largest_idle_instance(instance_group_name=instance_group.name, capacity_type=task.capacity_type)

                if execution_instance:
                    task.execution_node = execution_instance.hostname
                    # If our execution instance is a hybrid, prefer to do control tasks there as well.
                    if execution_instance.node_type == 'hybrid':
                        control_instance = execution_instance
                        task.controller_node = execution_instance.hostname

                    control_instance.consume_capacity(settings.AWX_CONTROL_NODE_TASK_IMPACT)
                    task.log_lifecycle("controller_node_chosen")
                    execution_instance.consume_capacity(task.task_impact)
                    task.log_lifecycle("execution_node_chosen")
                    logger.debug(
                        "Starting {} in group {} instance {} (remaining_capacity={})".format(
                            task.log_format, instance_group.name, execution_instance.hostname, execution_instance.remaining_capacity
                        )
                    )
                    execution_instance = self.instances[execution_instance.hostname].obj
                    self.dependency_graph.add_job(task)
                    self.start_task(task, instance_group, task.get_jobs_fail_chain(), execution_instance)
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

    def process_tasks(self, all_sorted_tasks):
        running_tasks = [t for t in all_sorted_tasks if t.status in ['waiting', 'running']]
        self.process_running_tasks(running_tasks)
        self.subsystem_metrics.inc(f"{self.prefix}_running_processed", len(running_tasks))

        pending_tasks = [t for t in all_sorted_tasks if t.status == 'pending']

        self.process_pending_tasks(pending_tasks)
        self.subsystem_metrics.inc(f"{self.prefix}_pending_processed", len(pending_tasks))

    @timeit
    def _schedule(self):
        all_sorted_tasks = self.get_tasks(dict(status__in=["pending", "waiting", "running"], dependencies_processed=True))

        self.after_lock_init(all_sorted_tasks)
        self.reap_jobs_from_orphaned_instances()

        if len(all_sorted_tasks) > 0:
            self.process_tasks(all_sorted_tasks)
