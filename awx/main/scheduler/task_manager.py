# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import datetime, timedelta
import logging
import uuid
import json
from sets import Set

# Django
from django.conf import settings
from django.core.cache import cache
from django.db import transaction, connection, DatabaseError
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now as tz_now, utc
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

# AWX
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
    WorkflowJob,
)
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.main.utils.pglock import advisory_lock
from awx.main.utils import get_type_for_model
from awx.main.signals import disable_activity_stream

from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main import tasks as awx_tasks
from awx.main.utils import decrypt_field

# Celery
from celery.task.control import inspect


logger = logging.getLogger('awx.main.scheduler')


class TaskManager():

    def __init__(self):
        self.graph = dict()
        for rampart_group in InstanceGroup.objects.prefetch_related('instances'):
            self.graph[rampart_group.name] = dict(graph=DependencyGraph(rampart_group.name),
                                                  capacity_total=rampart_group.capacity,
                                                  consumed_capacity=0)

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
        inventory_updates_qs = InventoryUpdate.objects.filter(status__in=status_list).exclude(source='file').prefetch_related('inventory_source', 'instance_group')
        inventory_updates = [i for i in inventory_updates_qs]
        project_updates = [p for p in ProjectUpdate.objects.filter(status__in=status_list).prefetch_related('instance_group')]
        system_jobs = [s for s in SystemJob.objects.filter(status__in=status_list).prefetch_related('instance_group')]
        ad_hoc_commands = [a for a in AdHocCommand.objects.filter(status__in=status_list).prefetch_related('instance_group')]
        workflow_jobs = [w for w in WorkflowJob.objects.filter(status__in=status_list)]
        all_tasks = sorted(jobs + project_updates + inventory_updates + system_jobs + ad_hoc_commands + workflow_jobs,
                           key=lambda task: task.created)
        return all_tasks

    '''
    Tasks that are running and SHOULD have a celery task.
    {
        'execution_node': [j1, j2,...],
        'execution_node': [j3],
        ...
    }
    '''
    def get_running_tasks(self):
        execution_nodes = {}
        waiting_jobs = []
        now = tz_now()
        workflow_ctype_id = ContentType.objects.get_for_model(WorkflowJob).id
        jobs = UnifiedJob.objects.filter((Q(status='running') |
                                         Q(status='waiting', modified__lte=now - timedelta(seconds=60))) &
                                         ~Q(polymorphic_ctype_id=workflow_ctype_id))
        for j in jobs:
            if j.execution_node:
                execution_nodes.setdefault(j.execution_node, []).append(j)
            else:
                waiting_jobs.append(j)
        return (execution_nodes, waiting_jobs)

    '''
    Tasks that are currently running in celery

    Transform:
    {
        "celery@ec2-54-204-222-62.compute-1.amazonaws.com": [],
        "celery@ec2-54-163-144-168.compute-1.amazonaws.com": [{
            ...
            "id": "5238466a-f8c7-43b3-9180-5b78e9da8304",
            ...
        }, {
            ...,
        }, ...]
    }

    to:
    {
        "ec2-54-204-222-62.compute-1.amazonaws.com": [
            "5238466a-f8c7-43b3-9180-5b78e9da8304",
            "5238466a-f8c7-43b3-9180-5b78e9da8306",
            ...
        ]
    }
    '''
    def get_active_tasks(self):
        inspector = inspect()
        if not hasattr(settings, 'IGNORE_CELERY_INSPECTOR'):
            active_task_queues = inspector.active()
        else:
            logger.warn("Ignoring celery task inspector")
            active_task_queues = None

        queues = None

        if active_task_queues is not None:
            queues = {}
            for queue in active_task_queues:
                active_tasks = set()
                map(lambda at: active_tasks.add(at['id']), active_task_queues[queue])

                # celery worker name is of the form celery@myhost.com
                queue_name = queue.split('@')
                queue_name = queue_name[1 if len(queue_name) > 1 else 0]
                queues[queue_name] = active_tasks
        else:
            if not hasattr(settings, 'CELERY_UNIT_TEST'):
                return (None, None)

        return (active_task_queues, queues)

    def get_latest_project_update_tasks(self, all_sorted_tasks):
        project_ids = Set()
        for task in all_sorted_tasks:
            if isinstance(task, Job):
                project_ids.add(task.project_id)
        return ProjectUpdate.objects.filter(id__in=project_ids)

    def get_latest_inventory_update_tasks(self, all_sorted_tasks):
        inventory_ids = Set()
        for task in all_sorted_tasks:
            if isinstance(task, Job):
                inventory_ids.add(task.inventory_id)
        return InventoryUpdate.objects.filter(id__in=inventory_ids)

    def get_running_workflow_jobs(self):
        graph_workflow_jobs = [wf for wf in
                               WorkflowJob.objects.filter(status='running')]
        return graph_workflow_jobs

    def get_inventory_source_tasks(self, all_sorted_tasks):
        inventory_ids = Set()
        for task in all_sorted_tasks:
            if isinstance(task, Job):
                inventory_ids.add(task.inventory_id)
        return [invsrc for invsrc in InventorySource.objects.filter(inventory_id__in=inventory_ids, update_on_launch=True)]

    def spawn_workflow_graph_jobs(self, workflow_jobs):
        for workflow_job in workflow_jobs:
            dag = WorkflowDAG(workflow_job)
            spawn_nodes = dag.bfs_nodes_to_run()
            for spawn_node in spawn_nodes:
                if spawn_node.unified_job_template is None:
                    continue
                kv = spawn_node.get_job_kwargs()
                job = spawn_node.unified_job_template.create_unified_job(**kv)
                spawn_node.job = job
                spawn_node.save()
                if job._resources_sufficient_for_launch():
                    can_start = job.signal_start(**kv)
                    if not can_start:
                        job.job_explanation = _("Job spawned from workflow could not start because it "
                                                "was not in the right state or required manual credentials")
                else:
                    can_start = False
                    job.job_explanation = _("Job spawned from workflow could not start because it "
                                            "was missing a related resource such as project or inventory")
                if not can_start:
                    job.status = 'failed'
                    job.save(update_fields=['status', 'job_explanation'])
                    connection.on_commit(lambda: job.websocket_emit_status('failed'))

                # TODO: should we emit a status on the socket here similar to tasks.py awx_periodic_scheduler() ?
                #emit_websocket_notification('/socket.io/jobs', '', dict(id=))

    # See comment in tasks.py::RunWorkflowJob::run()
    def process_finished_workflow_jobs(self, workflow_jobs):
        result = []
        for workflow_job in workflow_jobs:
            dag = WorkflowDAG(workflow_job)
            if workflow_job.cancel_flag:
                workflow_job.status = 'canceled'
                workflow_job.save()
                dag.cancel_node_jobs()
                connection.on_commit(lambda: workflow_job.websocket_emit_status(workflow_job.status))
            elif dag.is_workflow_done():
                result.append(workflow_job.id)
                if workflow_job._has_failed():
                    workflow_job.status = 'failed'
                else:
                    workflow_job.status = 'successful'
                workflow_job.save()
                connection.on_commit(lambda: workflow_job.websocket_emit_status(workflow_job.status))
        return result

    def get_dependent_jobs_for_inv_and_proj_update(self, job_obj):
        return [{'type': j.model_to_str(), 'id': j.id} for j in job_obj.dependent_jobs.all()]

    def start_task(self, task, rampart_group, dependent_tasks=[]):
        from awx.main.tasks import handle_work_error, handle_work_success

        task_actual = {
            'type': get_type_for_model(type(task)),
            'id': task.id,
        }
        dependencies = [{'type': get_type_for_model(type(t)), 'id': t.id} for t in dependent_tasks]

        error_handler = handle_work_error.s(subtasks=[task_actual] + dependencies)
        success_handler = handle_work_success.s(task_actual=task_actual)

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
            if not task.supports_isolation() and rampart_group.controller_id:
                # non-Ansible jobs on isolated instances run on controller
                task.instance_group = rampart_group.controller
                logger.info('Submitting isolated %s to queue %s via %s.',
                            task.log_format, task.instance_group_id, rampart_group.controller_id)
            else:
                task.instance_group = rampart_group
                logger.info('Submitting %s to instance group %s.', task.log_format, task.instance_group_id)
            with disable_activity_stream():
                task.celery_task_id = str(uuid.uuid4())
                task.save()

            self.consume_capacity(task, rampart_group.name)

        def post_commit():
            task.websocket_emit_status(task.status)
            if task.status != 'failed':
                task.start_celery_task(opts, error_callback=error_handler, success_callback=success_handler, queue=rampart_group.name)

        connection.on_commit(post_commit)

    def process_running_tasks(self, running_tasks):
        map(lambda task: self.graph[task.instance_group.name]['graph'].add_job(task), running_tasks)

    def create_project_update(self, task):
        project_task = Project.objects.get(id=task.project_id).create_project_update(launch_type='dependency')

        # Project created 1 seconds behind
        project_task.created = task.created - timedelta(seconds=1)
        project_task.status = 'pending'
        project_task.save()
        return project_task

    def create_inventory_update(self, task, inventory_source_task):
        inventory_task = InventorySource.objects.get(id=inventory_source_task.id).create_inventory_update(launch_type='dependency')

        inventory_task.created = task.created - timedelta(seconds=2)
        inventory_task.status = 'pending'
        inventory_task.save()
        # inventory_sources = self.get_inventory_source_tasks([task])
        # self.process_inventory_sources(inventory_sources)
        return inventory_task

    def capture_chain_failure_dependencies(self, task, dependencies):
        with disable_activity_stream():
            task.dependent_jobs.add(*dependencies)

            for dep in dependencies:
                # Add task + all deps except self
                dep.dependent_jobs.add(*([task] + filter(lambda d: d != dep, dependencies)))

    def get_latest_inventory_update(self, inventory_source):
        latest_inventory_update = InventoryUpdate.objects.filter(inventory_source=inventory_source).order_by("-created")
        if not latest_inventory_update.exists():
            return None
        return latest_inventory_update.first()

    def should_update_inventory_source(self, job, latest_inventory_update):
        now = tz_now()

        # Already processed dependencies for this job
        if job.dependent_jobs.all():
            return False

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
        if job.dependent_jobs.all():
            return False

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

    def generate_dependencies(self, task):
        dependencies = []
        if type(task) is Job:
            # TODO: Can remove task.project None check after scan-job-default-playbook is removed
            if task.project is not None and task.project.scm_update_on_launch is True:
                latest_project_update = self.get_latest_project_update(task)
                if self.should_update_related_project(task, latest_project_update):
                    project_task = self.create_project_update(task)
                    dependencies.append(project_task)
                else:
                    if latest_project_update.status in ['waiting', 'pending', 'running']:
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
                    dependencies.append(inventory_task)
                else:
                    if latest_inventory_update.status in ['waiting', 'pending', 'running']:
                        dependencies.append(latest_inventory_update)

            if len(dependencies) > 0:
                self.capture_chain_failure_dependencies(task, dependencies)
        return dependencies

    def process_dependencies(self, dependent_task, dependency_tasks):
        for task in dependency_tasks:
            if self.is_job_blocked(task):
                logger.debug("Dependent %s is blocked from running", task.log_format)
                continue
            preferred_instance_groups = task.preferred_instance_groups
            found_acceptable_queue = False
            for rampart_group in preferred_instance_groups:
                if self.get_remaining_capacity(rampart_group.name) <= 0:
                    logger.debug("Skipping group %s capacity <= 0", rampart_group.name)
                    continue
                if not self.would_exceed_capacity(task, rampart_group.name):
                    logger.debug("Starting dependent %s in group %s", task.log_format, rampart_group.name)
                    self.graph[rampart_group.name]['graph'].add_job(task)
                    tasks_to_fail = filter(lambda t: t != task, dependency_tasks)
                    tasks_to_fail += [dependent_task]
                    self.start_task(task, rampart_group, tasks_to_fail)
                    found_acceptable_queue = True
            if not found_acceptable_queue:
                logger.debug("Dependent %s couldn't be scheduled on graph, waiting for next cycle", task.log_format)

    def process_pending_tasks(self, pending_tasks):
        for task in pending_tasks:
            self.process_dependencies(task, self.generate_dependencies(task))
            if self.is_job_blocked(task):
                logger.debug("%s is blocked from running", task.log_format)
                continue
            preferred_instance_groups = task.preferred_instance_groups
            found_acceptable_queue = False
            for rampart_group in preferred_instance_groups:
                remaining_capacity = self.get_remaining_capacity(rampart_group.name)
                if remaining_capacity <= 0:
                    logger.debug("Skipping group %s, remaining_capacity %s <= 0",
                                 rampart_group.name, remaining_capacity)
                    continue
                if not self.would_exceed_capacity(task, rampart_group.name):
                    logger.debug("Starting %s in group %s (remaining_capacity=%s)",
                                 task.log_format, rampart_group.name, remaining_capacity)
                    self.graph[rampart_group.name]['graph'].add_job(task)
                    self.start_task(task, rampart_group, task.get_jobs_fail_chain())
                    found_acceptable_queue = True
                    break
                else:
                    logger.debug("Not enough capacity to run %s on %s (remaining_capacity=%s)",
                                 task.log_format, rampart_group.name, remaining_capacity)
            if not found_acceptable_queue:
                logger.debug("%s couldn't be scheduled on graph, waiting for next cycle", task.log_format)

    def fail_jobs_if_not_in_celery(self, node_jobs, active_tasks, celery_task_start_time,
                                   isolated=False):
        for task in node_jobs:
            if (task.celery_task_id not in active_tasks and not hasattr(settings, 'IGNORE_CELERY_INSPECTOR')):
                if isinstance(task, WorkflowJob):
                    continue
                if task.modified > celery_task_start_time:
                    continue
                new_status = 'failed'
                if isolated:
                    new_status = 'error'
                task.status = new_status
                if isolated:
                    # TODO: cancel and reap artifacts of lost jobs from heartbeat
                    task.job_explanation += ' '.join((
                        'Task was marked as running in Tower but its ',
                        'controller management daemon was not present in',
                        'Celery, so it has been marked as failed.',
                        'Task may still be running, but contactability is unknown.'
                    ))
                else:
                    task.job_explanation += ' '.join((
                        'Task was marked as running in Tower but was not present in',
                        'Celery, so it has been marked as failed.',
                    ))
                try:
                    task.save(update_fields=['status', 'job_explanation'])
                except DatabaseError:
                    logger.error("Task {} DB error in marking failed. Job possibly deleted.".format(task.log_format))
                    continue
                awx_tasks._send_notification_templates(task, 'failed')
                task.websocket_emit_status(new_status)
                logger.error("{}Task {} has no record in celery. Marking as failed".format(
                    'Isolated ' if isolated else '', task.log_format))

    def cleanup_inconsistent_celery_tasks(self):
        '''
        Rectify tower db <-> celery inconsistent view of jobs state
        '''
        last_cleanup = cache.get('last_celery_task_cleanup') or datetime.min.replace(tzinfo=utc)
        if (tz_now() - last_cleanup).seconds < settings.AWX_INCONSISTENT_TASK_INTERVAL:
            return

        logger.debug("Failing inconsistent running jobs.")
        celery_task_start_time = tz_now()
        active_task_queues, active_queues = self.get_active_tasks()
        cache.set('last_celery_task_cleanup', tz_now())

        if active_queues is None:
            logger.error('Failed to retrieve active tasks from celery')
            return None

        '''
        Only consider failing tasks on instances for which we obtained a task 
        list from celery for.
        '''
        running_tasks, waiting_tasks = self.get_running_tasks()
        all_celery_task_ids = []
        for node, node_jobs in active_queues.iteritems():
            all_celery_task_ids.extend(node_jobs)

        self.fail_jobs_if_not_in_celery(waiting_tasks, all_celery_task_ids, celery_task_start_time)

        for node, node_jobs in running_tasks.iteritems():
            isolated = False
            if node in active_queues:
                active_tasks = active_queues[node]
            else:
                '''
                Node task list not found in celery. We may branch into cases:
                 - instance is unknown to tower, system is improperly configured
                 - instance is reported as down, then fail all jobs on the node
                 - instance is an isolated node, then check running tasks
                   among all allowed controller nodes for management process
                 - valid healthy instance not included in celery task list
                   probably a netsplit case, leave it alone
                '''
                instance = Instance.objects.filter(hostname=node).first()

                if instance is None:
                    logger.error("Execution node Instance {} not found in database. "
                                 "The node is currently executing jobs {}".format(
                                     node, [j.log_format for j in node_jobs]))
                    active_tasks = []
                elif instance.capacity == 0:
                    active_tasks = []
                elif instance.rampart_groups.filter(controller__isnull=False).exists():
                    active_tasks = all_celery_task_ids
                    isolated = True
                else:
                    continue

            self.fail_jobs_if_not_in_celery(
                node_jobs, active_tasks, celery_task_start_time,
                isolated=isolated
            )

    def calculate_capacity_consumed(self, tasks):
        self.graph = InstanceGroup.objects.capacity_values(tasks=tasks, graph=self.graph)

    def would_exceed_capacity(self, task, instance_group):
        current_capacity = self.graph[instance_group]['consumed_capacity']
        capacity_total = self.graph[instance_group]['capacity_total']
        if current_capacity == 0:
            return False
        return (task.task_impact + current_capacity > capacity_total)

    def consume_capacity(self, task, instance_group):
        logger.debug('%s consumed %s capacity units from %s with prior total of %s',
                     task.log_format, task.task_impact, instance_group,
                     self.graph[instance_group]['consumed_capacity'])
        self.graph[instance_group]['consumed_capacity'] += task.task_impact

    def get_remaining_capacity(self, instance_group):
        return (self.graph[instance_group]['capacity_total'] - self.graph[instance_group]['consumed_capacity'])

    def process_tasks(self, all_sorted_tasks):
        running_tasks = filter(lambda t: t.status in ['waiting', 'running'], all_sorted_tasks)

        self.calculate_capacity_consumed(running_tasks)

        self.process_running_tasks(running_tasks)

        pending_tasks = filter(lambda t: t.status in 'pending', all_sorted_tasks)
        self.process_pending_tasks(pending_tasks)

    def _schedule(self):
        finished_wfjs = []
        all_sorted_tasks = self.get_tasks()
        if len(all_sorted_tasks) > 0:
            # TODO: Deal with
            # latest_project_updates = self.get_latest_project_update_tasks(all_sorted_tasks)
            # self.process_latest_project_updates(latest_project_updates)

            # latest_inventory_updates = self.get_latest_inventory_update_tasks(all_sorted_tasks)
            # self.process_latest_inventory_updates(latest_inventory_updates)

            self.all_inventory_sources = self.get_inventory_source_tasks(all_sorted_tasks)

            running_workflow_tasks = self.get_running_workflow_jobs()
            finished_wfjs = self.process_finished_workflow_jobs(running_workflow_tasks)

            self.spawn_workflow_graph_jobs(running_workflow_tasks)

            self.process_tasks(all_sorted_tasks)
        return finished_wfjs

    def schedule(self):
        with transaction.atomic():
            # Lock
            with advisory_lock('task_manager_lock', wait=False) as acquired:
                if acquired is False:
                    logger.debug("Not running scheduler, another task holds lock")
                    return
                logger.debug("Starting Scheduler")

                self.cleanup_inconsistent_celery_tasks()
                finished_wfjs = self._schedule()

                # Operations whose queries rely on modifications made during the atomic scheduling session
                for wfj in WorkflowJob.objects.filter(id__in=finished_wfjs):
                    awx_tasks._send_notification_templates(wfj, 'succeeded' if wfj.status == 'successful' else 'failed')
