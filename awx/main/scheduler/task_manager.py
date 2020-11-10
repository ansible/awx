# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import timedelta
import logging
import uuid
import json
import random
from types import SimpleNamespace

# Django
from django.db import transaction, connection
from django.utils.translation import ugettext_lazy as _, gettext_noop
from django.utils.timezone import now as tz_now
from django.conf import settings
from django.db.models import Q

# AWX
from awx.main.dispatch.reaper import reap_job
from awx.main.models import (
    AdHocCommand,
    Instance,
    InstanceGroup,
    InventorySource,
    InventoryUpdate,
    Job,
    Project,
    ProjectUpdate,
    SystemJob,
    UnifiedJob,
    WorkflowApproval,
    WorkflowJob,
    WorkflowJobTemplate
)
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.main.utils.pglock import advisory_lock
from awx.main.utils import get_type_for_model, task_manager_bulk_reschedule, schedule_task_manager
from awx.main.signals import disable_activity_stream
from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.utils import decrypt_field


logger = logging.getLogger('awx.main.scheduler')


class TaskManager():

    def __init__(self):
        '''
        Do NOT put database queries or other potentially expensive operations
        in the task manager init. The task manager object is created every time a
        job is created, transitions state, and every 30 seconds on each tower node.
        More often then not, the object is destroyed quickly because the NOOP case is hit.

        The NOOP case is short-circuit logic. If the task manager realizes that another instance
        of the task manager is already running, then it short-circuits and decides not to run.
        '''
        self.graph = dict()
        # start task limit indicates how many pending jobs can be started on this
        # .schedule() run. Starting jobs is expensive, and there is code in place to reap
        # the task manager after 5 minutes. At scale, the task manager can easily take more than
        # 5 minutes to start pending jobs. If this limit is reached, pending jobs
        # will no longer be started and will be started on the next task manager cycle.
        self.start_task_limit = settings.START_TASK_LIMIT

    def after_lock_init(self):
        '''
        Init AFTER we know this instance of the task manager will run because the lock is acquired.
        '''
        instances = Instance.objects.filter(~Q(hostname=None), capacity__gt=0, enabled=True)
        self.real_instances = {i.hostname: i for i in instances}

        instances_partial = [SimpleNamespace(obj=instance,
                                             remaining_capacity=instance.remaining_capacity,
                                             capacity=instance.capacity,
                                             jobs_running=instance.jobs_running,
                                             hostname=instance.hostname) for instance in instances]

        instances_by_hostname = {i.hostname: i for i in instances_partial}

        for rampart_group in InstanceGroup.objects.prefetch_related('instances'):
            self.graph[rampart_group.name] = dict(graph=DependencyGraph(rampart_group.name),
                                                  capacity_total=rampart_group.capacity,
                                                  consumed_capacity=0,
                                                  instances=[])
            for instance in rampart_group.instances.filter(capacity__gt=0, enabled=True).order_by('hostname'):
                if instance.hostname in instances_by_hostname:
                    self.graph[rampart_group.name]['instances'].append(instances_by_hostname[instance.hostname])

    def is_job_blocked(self, task):
        # TODO: I'm not happy with this, I think blocking behavior should be decided outside of the dependency graph
        #       in the old task manager this was handled as a method on each task object outside of the graph and
        #       probably has the side effect of cutting down *a lot* of the logic from this task manager class
        for g in self.graph:
            if self.graph[g]['graph'].is_job_blocked(task):
                return True

        if not task.dependent_jobs_finished():
            return True

        return False

    def get_tasks(self, status_list=('pending', 'waiting', 'running')):
        jobs = [j for j in Job.objects.filter(status__in=status_list).prefetch_related('instance_group')]
        inventory_updates_qs = InventoryUpdate.objects.filter(
            status__in=status_list).exclude(source='file').prefetch_related('inventory_source', 'instance_group')
        inventory_updates = [i for i in inventory_updates_qs]
        # Notice the job_type='check': we want to prevent implicit project updates from blocking our jobs.
        project_updates = [p for p in ProjectUpdate.objects.filter(status__in=status_list, job_type='check').prefetch_related('instance_group')]
        system_jobs = [s for s in SystemJob.objects.filter(status__in=status_list).prefetch_related('instance_group')]
        ad_hoc_commands = [a for a in AdHocCommand.objects.filter(status__in=status_list).prefetch_related('instance_group')]
        workflow_jobs = [w for w in WorkflowJob.objects.filter(status__in=status_list)]
        all_tasks = sorted(jobs + project_updates + inventory_updates + system_jobs + ad_hoc_commands + workflow_jobs,
                           key=lambda task: task.created)
        return all_tasks

    def get_running_workflow_jobs(self):
        graph_workflow_jobs = [wf for wf in
                               WorkflowJob.objects.filter(status='running')]
        return graph_workflow_jobs

    def get_inventory_source_tasks(self, all_sorted_tasks):
        inventory_ids = set()
        for task in all_sorted_tasks:
            if isinstance(task, Job):
                inventory_ids.add(task.inventory_id)
        return [invsrc for invsrc in InventorySource.objects.filter(inventory_id__in=inventory_ids, update_on_launch=True)]

    def spawn_workflow_graph_jobs(self, workflow_jobs):
        for workflow_job in workflow_jobs:
            if workflow_job.cancel_flag:
                logger.debug('Not spawning jobs for %s because it is pending cancelation.', workflow_job.log_format)
                continue
            dag = WorkflowDAG(workflow_job)
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
                        logger.info('Refusing to start recursive workflow-in-workflow id={}, wfjt={}, ancestors={}'.format(
                            job.id, spawn_node.unified_job_template.pk, [wa.pk for wa in workflow_ancestors]))
                        display_list = [spawn_node.unified_job_template] + workflow_ancestors
                        job.job_explanation = gettext_noop(
                            "Workflow Job spawned from workflow could not start because it "
                            "would result in recursion (spawn order, most recent first: {})"
                        ).format(', '.join(['<{}>'.format(tmp) for tmp in display_list]))
                    else:
                        logger.debug('Starting workflow-in-workflow id={}, wfjt={}, ancestors={}'.format(
                            job.id, spawn_node.unified_job_template.pk, [wa.pk for wa in workflow_ancestors]))
                if not job._resources_sufficient_for_launch():
                    can_start = False
                    job.job_explanation = gettext_noop("Job spawned from workflow could not start because it "
                                                       "was missing a related resource such as project or inventory")
                if can_start:
                    if workflow_job.start_args:
                        start_args = json.loads(decrypt_field(workflow_job, 'start_args'))
                    else:
                        start_args = {}
                    can_start = job.signal_start(**start_args)
                    if not can_start:
                        job.job_explanation = gettext_noop("Job spawned from workflow could not start because it "
                                                           "was not in the right state or required manual credentials")
                if not can_start:
                    job.status = 'failed'
                    job.save(update_fields=['status', 'job_explanation'])
                    job.websocket_emit_status('failed')

                # TODO: should we emit a status on the socket here similar to tasks.py awx_periodic_scheduler() ?
                #emit_websocket_notification('/socket.io/jobs', '', dict(id=))

    def process_finished_workflow_jobs(self, workflow_jobs):
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
                for n in workflow_nodes:
                    n.save(update_fields=['do_not_run'])
                is_done = dag.is_workflow_done()
                if not is_done:
                    continue
                has_failed, reason = dag.has_workflow_failed()
                logger.debug('Marking %s as %s.', workflow_job.log_format, 'failed' if has_failed else 'successful')
                result.append(workflow_job.id)
                new_status = 'failed' if has_failed else 'successful'
                logger.debug("Transitioning {} to {} status.".format(workflow_job.log_format, new_status))
                update_fields = ['status', 'start_args']
                workflow_job.status = new_status
                if reason:
                    logger.info(reason)
                    workflow_job.job_explanation = gettext_noop("No error handling paths found, marking workflow as failed")
                    update_fields.append('job_explanation')
                workflow_job.start_args = ''  # blank field to remove encrypted passwords
                workflow_job.save(update_fields=update_fields)
                status_changed = True
            if status_changed:
                workflow_job.websocket_emit_status(workflow_job.status)
                # Operations whose queries rely on modifications made during the atomic scheduling session
                workflow_job.send_notification_templates('succeeded' if workflow_job.status == 'successful' else 'failed')
                if workflow_job.spawned_by_workflow:
                    schedule_task_manager()
        return result

    def start_task(self, task, rampart_group, dependent_tasks=None, instance=None):
        self.start_task_limit -= 1
        if self.start_task_limit == 0:
            # schedule another run immediately after this task manager
            schedule_task_manager()
        from awx.main.tasks import handle_work_error, handle_work_success

        dependent_tasks = dependent_tasks or []

        task_actual = {
            'type': get_type_for_model(type(task)),
            'id': task.id,
        }
        dependencies = [{'type': get_type_for_model(type(t)), 'id': t.id} for t in dependent_tasks]

        controller_node = None
        if task.supports_isolation() and rampart_group.controller_id:
            try:
                controller_node = rampart_group.choose_online_controller_node()
            except IndexError:
                logger.debug("No controllers available in group {} to run {}".format(
                             rampart_group.name, task.log_format))
                return

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
            if type(task) is WorkflowJob:
                task.status = 'running'
                task.send_notification_templates('running')
                logger.debug('Transitioning %s to running status.', task.log_format)
                schedule_task_manager()
            elif not task.supports_isolation() and rampart_group.controller_id:
                # non-Ansible jobs on isolated instances run on controller
                task.instance_group = rampart_group.controller
                task.execution_node = random.choice(list(rampart_group.controller.instances.all().values_list('hostname', flat=True)))
                logger.debug('Submitting isolated {} to queue {} on node {}.'.format(
                             task.log_format, task.instance_group.name, task.execution_node))
            elif controller_node:
                task.instance_group = rampart_group
                task.execution_node = instance.hostname
                task.controller_node = controller_node
                logger.debug('Submitting isolated {} to queue {} controlled by {}.'.format(
                             task.log_format, task.execution_node, controller_node))
            elif rampart_group.is_containerized:
                # find one real, non-containerized instance with capacity to
                # act as the controller for k8s API interaction
                match = None
                for group in InstanceGroup.objects.all():
                    if group.is_containerized or group.controller_id:
                        continue
                    match = group.fit_task_to_most_remaining_capacity_instance(task, group.instances.all())
                    if match:
                        break
                task.instance_group = rampart_group
                if match is None:
                    logger.warn(
                        'No available capacity to run containerized <{}>.'.format(task.log_format)
                    )
                else:
                    if task.supports_isolation():
                        task.controller_node = match.hostname
                    else:
                        # project updates and inventory updates don't *actually* run in pods,
                        # so just pick *any* non-isolated, non-containerized host and use it
                        # as the execution node
                        task.execution_node = match.hostname
                        logger.debug('Submitting containerized {} to queue {}.'.format(
                                     task.log_format, task.execution_node))
            else:
                task.instance_group = rampart_group
                if instance is not None:
                    task.execution_node = instance.hostname
                logger.debug('Submitting {} to <instance group, instance> <{},{}>.'.format(
                             task.log_format, task.instance_group_id, task.execution_node))
            with disable_activity_stream():
                task.celery_task_id = str(uuid.uuid4())
                task.save()

            if rampart_group is not None:
                self.consume_capacity(task, rampart_group.name)

        def post_commit():
            if task.status != 'failed' and type(task) is not WorkflowJob:
                task_cls = task._get_task_class()
                task_cls.apply_async(
                    [task.pk],
                    opts,
                    queue=task.get_queue_name(),
                    uuid=task.celery_task_id,
                    callbacks=[{
                        'task': handle_work_success.name,
                        'kwargs': {'task_actual': task_actual}
                    }],
                    errbacks=[{
                        'task': handle_work_error.name,
                        'args': [task.celery_task_id],
                        'kwargs': {'subtasks': [task_actual] + dependencies}
                    }],
                )

        task.websocket_emit_status(task.status)  # adds to on_commit
        connection.on_commit(post_commit)

    def process_running_tasks(self, running_tasks):
        for task in running_tasks:
            if task.instance_group:
                self.graph[task.instance_group.name]['graph'].add_job(task)

    def create_project_update(self, task):
        project_task = Project.objects.get(id=task.project_id).create_project_update(
            _eager_fields=dict(launch_type='dependency'))

        # Project created 1 seconds behind
        project_task.created = task.created - timedelta(seconds=1)
        project_task.status = 'pending'
        project_task.save()
        logger.debug(
            'Spawned {} as dependency of {}'.format(
                project_task.log_format, task.log_format
            )
        )
        return project_task

    def create_inventory_update(self, task, inventory_source_task):
        inventory_task = InventorySource.objects.get(id=inventory_source_task.id).create_inventory_update(
            _eager_fields=dict(launch_type='dependency'))

        inventory_task.created = task.created - timedelta(seconds=2)
        inventory_task.status = 'pending'
        inventory_task.save()
        logger.debug(
            'Spawned {} as dependency of {}'.format(
                inventory_task.log_format, task.log_format
            )
        )
        # inventory_sources = self.get_inventory_source_tasks([task])
        # self.process_inventory_sources(inventory_sources)
        return inventory_task

    def capture_chain_failure_dependencies(self, task, dependencies):
        with disable_activity_stream():
            task.dependent_jobs.add(*dependencies)

            for dep in dependencies:
                # Add task + all deps except self
                dep.dependent_jobs.add(*([task] + [d for d in dependencies if d != dep]))

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
        if latest_inventory_update.inventory_source.update_on_launch is True and \
                latest_inventory_update.status in ['failed', 'canceled', 'error']:
            return True
        return False

    def get_latest_project_update(self, job):
        latest_project_update = ProjectUpdate.objects.filter(project=job.project, job_type='check').order_by("-created")
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
        if latest_project_update.project.scm_update_cache_timeout == 0 and \
           latest_project_update.launch_type == 'dependency' and \
           latest_project_update.created == job.created - timedelta(seconds=1):
            return False
        '''
        Normal Cache Timeout Logic
        '''
        timeout_seconds = timedelta(seconds=latest_project_update.project.scm_update_cache_timeout)
        if (latest_project_update.finished + timeout_seconds) < now:
            return True
        return False

    def generate_dependencies(self, undeped_tasks):
        created_dependencies = []
        for task in undeped_tasks:
            dependencies = []
            if not type(task) is Job:
                continue
            # TODO: Can remove task.project None check after scan-job-default-playbook is removed
            if task.project is not None and task.project.scm_update_on_launch is True:
                latest_project_update = self.get_latest_project_update(task)
                if self.should_update_related_project(task, latest_project_update):
                    project_task = self.create_project_update(task)
                    created_dependencies.append(project_task)
                    dependencies.append(project_task)
                else:
                    dependencies.append(latest_project_update)

            # Inventory created 2 seconds behind job
            try:
                start_args = json.loads(decrypt_field(task, field_name="start_args"))
            except ValueError:
                start_args = dict()
            for inventory_source in [invsrc for invsrc in self.all_inventory_sources if invsrc.inventory == task.inventory]:
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

            if len(dependencies) > 0:
                self.capture_chain_failure_dependencies(task, dependencies)

        UnifiedJob.objects.filter(pk__in = [task.pk for task in undeped_tasks]).update(dependencies_processed=True)
        return created_dependencies

    def process_pending_tasks(self, pending_tasks):
        running_workflow_templates = set([wf.unified_job_template_id for wf in self.get_running_workflow_jobs()])
        for task in pending_tasks:
            if self.start_task_limit <= 0:
                break
            if self.is_job_blocked(task):
                logger.debug("{} is blocked from running".format(task.log_format))
                continue
            preferred_instance_groups = task.preferred_instance_groups
            found_acceptable_queue = False
            if isinstance(task, WorkflowJob):
                if task.unified_job_template_id in running_workflow_templates:
                    if not task.allow_simultaneous:
                        logger.debug("{} is blocked from running, workflow already running".format(task.log_format))
                        continue
                else:
                    running_workflow_templates.add(task.unified_job_template_id)
                self.start_task(task, None, task.get_jobs_fail_chain(), None)
                continue
            for rampart_group in preferred_instance_groups:
                if task.can_run_containerized and rampart_group.is_containerized:
                    self.graph[rampart_group.name]['graph'].add_job(task)
                    self.start_task(task, rampart_group, task.get_jobs_fail_chain(), None)
                    found_acceptable_queue = True
                    break

                remaining_capacity = self.get_remaining_capacity(rampart_group.name)
                if not rampart_group.is_containerized and self.get_remaining_capacity(rampart_group.name) <= 0:
                    logger.debug("Skipping group {}, remaining_capacity {} <= 0".format(
                                 rampart_group.name, remaining_capacity))
                    continue

                execution_instance = InstanceGroup.fit_task_to_most_remaining_capacity_instance(task, self.graph[rampart_group.name]['instances']) or \
                    InstanceGroup.find_largest_idle_instance(self.graph[rampart_group.name]['instances'])

                if execution_instance or rampart_group.is_containerized:
                    if not rampart_group.is_containerized:
                        execution_instance.remaining_capacity = max(0, execution_instance.remaining_capacity - task.task_impact)
                        execution_instance.jobs_running += 1
                        logger.debug("Starting {} in group {} instance {} (remaining_capacity={})".format(
                                     task.log_format, rampart_group.name, execution_instance.hostname, remaining_capacity))

                    if execution_instance:
                        execution_instance = self.real_instances[execution_instance.hostname]
                    self.graph[rampart_group.name]['graph'].add_job(task)
                    self.start_task(task, rampart_group, task.get_jobs_fail_chain(), execution_instance)
                    found_acceptable_queue = True
                    break
                else:
                    logger.debug("No instance available in group {} to run job {} w/ capacity requirement {}".format(
                                 rampart_group.name, task.log_format, task.task_impact))
            if not found_acceptable_queue:
                logger.debug("{} couldn't be scheduled on graph, waiting for next cycle".format(task.log_format))

    def timeout_approval_node(self):
        workflow_approvals = WorkflowApproval.objects.filter(status='pending')
        now = tz_now()
        for task in workflow_approvals:
            approval_timeout_seconds = timedelta(seconds=task.timeout)
            if task.timeout == 0:
                continue
            if (now - task.created) >= approval_timeout_seconds:
                timeout_message = _(
                    "The approval node {name} ({pk}) has expired after {timeout} seconds."
                ).format(name=task.name, pk=task.pk, timeout=task.timeout)
                logger.warn(timeout_message)
                task.timed_out = True
                task.status = 'failed'
                task.send_approval_notification('timed_out')
                task.websocket_emit_status(task.status)
                task.job_explanation = timeout_message
                task.save(update_fields=['status', 'job_explanation', 'timed_out'])

    def reap_jobs_from_orphaned_instances(self):
        # discover jobs that are in running state but aren't on an execution node
        # that we know about; this is a fairly rare event, but it can occur if you,
        # for example, SQL backup an awx install with running jobs and restore it
        # elsewhere
        for j in UnifiedJob.objects.filter(
            status__in=['pending', 'waiting', 'running'],
        ).exclude(
            execution_node__in=Instance.objects.values_list('hostname', flat=True)
        ):
            if j.execution_node and not j.is_containerized:
                logger.error(f'{j.execution_node} is not a registered instance; reaping {j.log_format}')
                reap_job(j, 'failed')

    def calculate_capacity_consumed(self, tasks):
        self.graph = InstanceGroup.objects.capacity_values(tasks=tasks, graph=self.graph)

    def consume_capacity(self, task, instance_group):
        logger.debug('{} consumed {} capacity units from {} with prior total of {}'.format(
                     task.log_format, task.task_impact, instance_group,
                     self.graph[instance_group]['consumed_capacity']))
        self.graph[instance_group]['consumed_capacity'] += task.task_impact

    def get_remaining_capacity(self, instance_group):
        return (self.graph[instance_group]['capacity_total'] - self.graph[instance_group]['consumed_capacity'])

    def process_tasks(self, all_sorted_tasks):
        running_tasks = [t for t in all_sorted_tasks if t.status in ['waiting', 'running']]

        self.calculate_capacity_consumed(running_tasks)

        self.process_running_tasks(running_tasks)

        pending_tasks = [t for t in all_sorted_tasks if t.status == 'pending']
        undeped_tasks = [t for t in pending_tasks if not t.dependencies_processed]
        dependencies = self.generate_dependencies(undeped_tasks)
        self.process_pending_tasks(dependencies)
        self.process_pending_tasks(pending_tasks)

    def _schedule(self):
        finished_wfjs = []
        all_sorted_tasks = self.get_tasks()

        self.after_lock_init()

        if len(all_sorted_tasks) > 0:
            # TODO: Deal with
            # latest_project_updates = self.get_latest_project_update_tasks(all_sorted_tasks)
            # self.process_latest_project_updates(latest_project_updates)

            # latest_inventory_updates = self.get_latest_inventory_update_tasks(all_sorted_tasks)
            # self.process_latest_inventory_updates(latest_inventory_updates)

            self.all_inventory_sources = self.get_inventory_source_tasks(all_sorted_tasks)

            running_workflow_tasks = self.get_running_workflow_jobs()
            finished_wfjs = self.process_finished_workflow_jobs(running_workflow_tasks)

            previously_running_workflow_tasks = running_workflow_tasks
            running_workflow_tasks = []
            for workflow_job in previously_running_workflow_tasks:
                if workflow_job.status == 'running':
                    running_workflow_tasks.append(workflow_job)
                else:
                    logger.debug('Removed %s from job spawning consideration.', workflow_job.log_format)

            self.spawn_workflow_graph_jobs(running_workflow_tasks)

            self.timeout_approval_node()
            self.reap_jobs_from_orphaned_instances()

            self.process_tasks(all_sorted_tasks)
        return finished_wfjs

    def schedule(self):
        # Lock
        with advisory_lock('task_manager_lock', wait=False) as acquired:
            with transaction.atomic():
                if acquired is False:
                    logger.debug("Not running scheduler, another task holds lock")
                    return
                logger.debug("Starting Scheduler")
                with task_manager_bulk_reschedule():
                    self._schedule()
                logger.debug("Finishing Scheduler")
