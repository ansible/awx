# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import timedelta
import logging
from sets import Set

# Django
from django.conf import settings
from django.db import transaction, connection
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now as tz_now

# AWX
from awx.main.models import * # noqa
#from awx.main.scheduler.dag_simple import SimpleDAG
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.main.utils.pglock import advisory_lock

from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.tasks import _send_notification_templates

# Celery
from celery.task.control import inspect


logger = logging.getLogger('awx.main.scheduler')


class TaskManager():

    def __init__(self):
        self.graph = dict()
        for rampart_group in InstanceGroup.objects.all():
            self.graph[rampart_group.name] = dict(graph=DependencyGraph(rampart_group.name),
                                                  capacity_total=rampart_group.capacity,
                                                  capacity_used=0)

    def is_job_blocked(self, task):
        # TODO: I'm not happy with this, I think blocking behavior should be decided outside of the dependency graph
        #       in the old task manager this was handled as a method on each task object outside of the graph and
        #       probably has the side effect of cutting down *a lot* of the logic from this task manager class
        for g in self.graph:
            if self.graph[g]['graph'].is_job_blocked(task):
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

    @classmethod
    def get_node_type(cls, obj):
        if type(obj) == Job:
            return "job"
        elif type(obj) == AdHocCommand:
            return "ad_hoc_command"
        elif type(obj) == InventoryUpdate:
            return "inventory_update"
        elif type(obj) == ProjectUpdate:
            return "project_update"
        elif type(obj) == SystemJob:
            return "system_job"
        elif type(obj) == WorkflowJob:
            return "workflow_job"
        return "unknown"

    '''
    Tasks that are running and SHOULD have a celery task.
    '''
    def get_running_tasks(self, all_tasks=None):
        if all_tasks is None:
            return self.get_tasks(status_list=('running',))
        return filter(lambda t: t.status == 'running', all_tasks)

    '''
    Tasks that are currently running in celery
    '''
    def get_active_tasks(self):
        inspector = inspect()
        if not hasattr(settings, 'IGNORE_CELERY_INSPECTOR'):
            active_task_queues = inspector.active()
        else:
            logger.warn("Ignoring celery task inspector")
            active_task_queues = None

        active_tasks = set()
        if active_task_queues is not None:
            for queue in active_task_queues:
                map(lambda at: active_tasks.add(at['id']), active_task_queues[queue])
        else:
            if not hasattr(settings, 'CELERY_UNIT_TEST'):
                return (None, None)

        return (active_task_queues, active_tasks)

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

                # TODO: should we emit a status on the socket here similar to tasks.py tower_periodic_scheduler() ?
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
            'type':self.get_node_type(task),
            'id': task.id,
        }
        dependencies = [{'type': self.get_node_type(t), 'id': t.id} for t in dependent_tasks]

        error_handler = handle_work_error.s(subtasks=[task_actual] + dependencies)
        success_handler = handle_work_success.s(task_actual=task_actual)

        '''
        This is to account for when there isn't enough capacity to execute all
        dependent jobs (i.e. proj or inv update) within the same schedule() 
        call.
        
        Proceeding calls to schedule() need to recontruct the proj or inv
        update -> job fail logic dependency. The below call recontructs that
        failure dependency.
        '''
        if len(dependencies) == 0:
            dependencies = self.get_dependent_jobs_for_inv_and_proj_update(task)
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
            else:
                task.instance_group = rampart_group
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
        for dep in dependencies:
            dep.dependent_jobs.add(task.id)
            dep.save()

    def should_update_inventory_source(self, job, inventory_source):
        now = tz_now()

        # Already processed dependencies for this job
        if job.dependent_jobs.all():
            return False
        latest_inventory_update = InventoryUpdate.objects.filter(inventory_source=inventory_source).order_by("created")
        if not latest_inventory_update.exists():
            return True
        latest_inventory_update = latest_inventory_update.first()
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

    def should_update_related_project(self, job):
        now = tz_now()
        if job.dependent_jobs.all():
            return False
        latest_project_update = ProjectUpdate.objects.filter(project=job.project).order_by("created")
        if not latest_project_update.exists():
            return True
        latest_project_update = latest_project_update.first()
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
            if task.project is not None and task.project.scm_update_on_launch is True and \
                    self.should_update_related_project(task):
                project_task = self.create_project_update(task)
                dependencies.append(project_task)
                # Inventory created 2 seconds behind job
            if task.launch_type != 'callback':
                for inventory_source in [invsrc for invsrc in self.all_inventory_sources if invsrc.inventory == task.inventory]:
                    if self.should_update_inventory_source(task, inventory_source):
                        inventory_task = self.create_inventory_update(task, inventory_source)
                        dependencies.append(inventory_task)
        self.capture_chain_failure_dependencies(task, dependencies)
        return dependencies

    def process_dependencies(self, dependent_task, dependency_tasks):
        for task in dependency_tasks:
            if self.is_job_blocked(task):
                logger.debug("Dependent task {} is blocked from running".format(task))
                continue
            preferred_instance_groups = task.preferred_instance_groups
            found_acceptable_queue = False
            for rampart_group in preferred_instance_groups:
                if self.get_remaining_capacity(rampart_group.name) <= 0:
                    logger.debug("Skipping group {} capacity <= 0".format(rampart_group.name))
                    continue
                if not self.would_exceed_capacity(task, rampart_group.name):
                    logger.debug("Starting dependent task {} in group {}".format(task, rampart_group.name))
                    self.graph[rampart_group.name]['graph'].add_job(task)
                    self.start_task(task, rampart_group, dependency_tasks)
                    found_acceptable_queue = True
            if not found_acceptable_queue:
                logger.debug("Dependent task {} couldn't be scheduled on graph, waiting for next cycle".format(task))

    def process_pending_tasks(self, pending_tasks):
        for task in pending_tasks:
            self.process_dependencies(task, self.generate_dependencies(task))
            if self.is_job_blocked(task):
                logger.debug("Task {} is blocked from running".format(task))
                continue
            preferred_instance_groups = task.preferred_instance_groups
            found_acceptable_queue = False
            for rampart_group in preferred_instance_groups:
                if self.get_remaining_capacity(rampart_group.name) <= 0:
                    logger.debug("Skipping group {} capacity <= 0".format(rampart_group.name))
                    continue
                if not self.would_exceed_capacity(task, rampart_group.name):
                    logger.debug("Starting task {} in group {}".format(task, rampart_group.name))
                    self.graph[rampart_group.name]['graph'].add_job(task)
                    self.start_task(task, rampart_group)
                    found_acceptable_queue = True
                    break
            if not found_acceptable_queue:
                logger.debug("Task {} couldn't be scheduled on graph, waiting for next cycle".format(task))

    def process_celery_tasks(self, celery_task_start_time, active_tasks, all_running_sorted_tasks):
        '''
        Rectify tower db <-> celery inconsistent view of jobs state
        '''
        for task in all_running_sorted_tasks:

            if (task.celery_task_id not in active_tasks and not hasattr(settings, 'IGNORE_CELERY_INSPECTOR')):
                # TODO: try catch the getting of the job. The job COULD have been deleted
                if isinstance(task, WorkflowJob):
                    continue
                if task_obj.modified > celery_task_start_time:
                    continue
                task.status = 'failed'
                task.job_explanation += ' '.join((
                    'Task was marked as running in Tower but was not present in',
                    'Celery, so it has been marked as failed.',
                ))
                task.save()
                _send_notification_templates(task, 'failed')
                task.websocket_emit_status('failed')
                logger.error("Task %s appears orphaned... marking as failed" % task)


    def calculate_capacity_used(self, tasks):
        for rampart_group in self.graph:
            self.graph[rampart_group]['capacity_used'] = 0
        for t in tasks:
            # TODO: dock capacity for isolated job management tasks running in queue
            for group_actual in InstanceGroup.objects.filter(instances__hostname=t.execution_node).values_list('name'):
                if group_actual[0] in self.graph:
                    self.graph[group_actual[0]]['capacity_used'] += t.task_impact

    def would_exceed_capacity(self, task, instance_group):
        current_capacity = self.graph[instance_group]['capacity_used']
        capacity_total = self.graph[instance_group]['capacity_total']
        if current_capacity == 0:
            return False
        return (task.task_impact + current_capacity > capacity_total)

    def consume_capacity(self, task, instance_group):
        self.graph[instance_group]['capacity_used'] += task.task_impact

    def get_remaining_capacity(self, instance_group):
        return (self.graph[instance_group]['capacity_total'] - self.graph[instance_group]['capacity_used'])

    def process_tasks(self, all_sorted_tasks):
        running_tasks = filter(lambda t: t.status in ['waiting', 'running'], all_sorted_tasks)

        self.calculate_capacity_used(running_tasks)

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
        logger.debug("Starting Schedule")
        with transaction.atomic():
            # Lock
            with advisory_lock('task_manager_lock', wait=False) as acquired:
                if acquired is False:
                    return

                finished_wfjs = self._schedule()

                # Operations whose queries rely on modifications made during the atomic scheduling session
                for wfj in WorkflowJob.objects.filter(id__in=finished_wfjs):
                    _send_notification_templates(wfj, 'succeeded' if wfj.status == 'successful' else 'failed')
