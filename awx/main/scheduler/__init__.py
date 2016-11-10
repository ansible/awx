#Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import timedelta
import logging
from sets import Set

# Django
from django.conf import settings
from django.db import transaction, connection
from django.db.utils import DatabaseError

# AWX
from awx.main.models import * # noqa
#from awx.main.scheduler.dag_simple import SimpleDAG
from awx.main.scheduler.dag_workflow import WorkflowDAG

from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.scheduler.partial import (
    JobDict, 
    ProjectUpdateDict, 
    ProjectUpdateLatestDict,
    InventoryUpdateDict,
    InventoryUpdateLatestDict,
    InventorySourceDict,
    SystemJobDict,
    AdHocCommandDict,
    WorkflowJobDict,
)
from awx.main.tasks import _send_notification_templates

# Celery
from celery.task.control import inspect

logger = logging.getLogger('awx.main.scheduler')

class TaskManager():
    def __init__(self):
        self.graph = DependencyGraph()
        self.capacity_total = Instance.objects.total_capacity()
        self.capacity_used = 0

    def get_tasks(self):
        status_list = ('pending', 'waiting', 'running')

        jobs = JobDict.filter_partial(status=status_list)
        inventory_updates = InventoryUpdateDict.filter_partial(status=status_list)
        project_updates = ProjectUpdateDict.filter_partial(status=status_list)
        system_jobs = SystemJobDict.filter_partial(status=status_list)
        ad_hoc_commands = AdHocCommandDict.filter_partial(status=status_list)
        workflow_jobs = WorkflowJobDict.filter_partial(status=status_list)

        all_actions = sorted(jobs + project_updates + inventory_updates + system_jobs + ad_hoc_commands + workflow_jobs,
                             key=lambda task: task['created'])
        return all_actions

    '''
    Tasks that are running and SHOULD have a celery task.
    '''
    def get_running_tasks(self):
        status_list = ('running',)

        jobs = JobDict.filter_partial(status=status_list)
        inventory_updates = InventoryUpdateDict.filter_partial(status=status_list)
        project_updates = ProjectUpdateDict.filter_partial(status=status_list)
        system_jobs = SystemJobDict.filter_partial(status=status_list)
        ad_hoc_commands = AdHocCommandDict.filter_partial(status=status_list)

        all_actions = sorted(jobs + project_updates + inventory_updates + system_jobs + ad_hoc_commands,
                             key=lambda task: task['created'])
        return all_actions

    # TODO: Consider a database query for this logic
    def get_latest_project_update_tasks(self, all_sorted_tasks):
        project_ids = Set()
        for task in all_sorted_tasks:
            if type(task) == JobDict:
                project_ids.add(task['project_id'])

        return ProjectUpdateLatestDict.filter_partial(list(project_ids))

    # TODO: Consider a database query for this logic
    def get_latest_inventory_update_tasks(self, all_sorted_tasks):
        inventory_ids = Set()
        for task in all_sorted_tasks:
            if type(task) == JobDict:
                inventory_ids.add(task['inventory_id'])

        return InventoryUpdateLatestDict.filter_partial(list(inventory_ids))


    def get_running_workflow_jobs(self):
        graph_workflow_jobs = [wf for wf in
                               WorkflowJob.objects.filter(status='running')]
        return graph_workflow_jobs

    # TODO: Consider a database query for this logic
    def get_inventory_source_tasks(self, all_sorted_tasks):
        inventory_ids = Set()
        results = []
        for task in all_sorted_tasks:
            if type(task) is JobDict:
                inventory_ids.add(task['inventory_id'])
        
        for inventory_id in inventory_ids:
            results.append((inventory_id, InventorySourceDict.filter_partial(inventory_id)))

        return results

    def spawn_workflow_graph_jobs(self, workflow_jobs):
        for workflow_job in workflow_jobs:
            dag = WorkflowDAG(workflow_job)
            spawn_nodes = dag.bfs_nodes_to_run()
            for spawn_node in spawn_nodes:
                kv = spawn_node.get_job_kwargs()
                job = spawn_node.unified_job_template.create_unified_job(**kv)
                spawn_node.job = job
                spawn_node.save()
                can_start = job.signal_start(**kv)
                if not can_start:
                    job.status = 'failed'
                    job.job_explanation = "Workflow job could not start because it was not in the right state or required manual credentials"
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

    def start_task(self, task, dependent_tasks=[]):
        from awx.main.tasks import handle_work_error, handle_work_success

        task_actual = {
            'type':task.get_job_type_str(),
            'id': task['id'],
        }
        dependencies = [{'type': t.get_job_type_str(), 'id': t['id']} for t in dependent_tasks]
        
        error_handler = handle_work_error.s(subtasks=[task_actual] + dependencies)
        success_handler = handle_work_success.s(task_actual=task_actual)
        
        job_obj = task.get_full()
        job_obj.status = 'waiting'

        (start_status, opts) = job_obj.pre_start()
        if not start_status:
            job_obj.status = 'failed'
            if job_obj.job_explanation:
                job_obj.job_explanation += ' '
            job_obj.job_explanation += 'Task failed pre-start check.'
            job_obj.save()
            # TODO: run error handler to fail sub-tasks and send notifications
        else:
            if type(job_obj) is WorkflowJob:
                job_obj.status = 'running'

            job_obj.save()

            self.consume_capacity(task)

        def post_commit():
            job_obj.websocket_emit_status(job_obj.status)
            if job_obj.status != 'failed':
                job_obj.start_celery_task(opts, error_callback=error_handler, success_callback=success_handler)
        
        connection.on_commit(post_commit)

    def process_runnable_tasks(self, runnable_tasks):
        map(lambda task: self.graph.add_job(task), runnable_tasks)

    def create_project_update(self, task):
        dep = Project.objects.get(id=task['project_id']).create_project_update(launch_type='dependency')

        # Project created 1 seconds behind
        dep.created = task['created'] - timedelta(seconds=1)
        dep.status = 'pending'
        dep.save()

        project_task = ProjectUpdateDict.get_partial(dep.id)

        return project_task

    def create_inventory_update(self, task, inventory_source_task):
        dep = InventorySource.objects.get(id=inventory_source_task['id']).create_inventory_update(launch_type='dependency')

        dep.created = task['created'] - timedelta(seconds=2)
        dep.status = 'pending'
        dep.save()

        inventory_task = InventoryUpdateDict.get_partial(dep.id)

        return inventory_task

    def generate_dependencies(self, task):
        dependencies = []
        # TODO: What if the project is null ?
        if type(task) is JobDict:
            if task['project__scm_update_on_launch'] is True and \
                    self.graph.should_update_related_project(task):
                project_task = self.create_project_update(task)
                dependencies.append(project_task)
                # Inventory created 2 seconds behind job

            inventory_sources_already_updated = task.get_inventory_sources_already_updated()

            for inventory_source_task in self.graph.get_inventory_sources(task['inventory_id']):
                if inventory_source_task['id'] in inventory_sources_already_updated:
                    print("Inventory already updated")
                    continue
                if self.graph.should_update_related_inventory_source(task, inventory_source_task['id']):
                    inventory_task = self.create_inventory_update(task, inventory_source_task)
                    dependencies.append(inventory_task)
        return dependencies

    def process_latest_project_updates(self, latest_project_updates):
        map(lambda task: self.graph.add_latest_project_update(task), latest_project_updates)

    def process_latest_inventory_updates(self, latest_inventory_updates):
        map(lambda task: self.graph.add_latest_inventory_update(task), latest_inventory_updates)

    def process_inventory_sources(self, inventory_id_sources):
        map(lambda (inventory_id, inventory_sources): self.graph.add_inventory_sources(inventory_id, inventory_sources), inventory_id_sources)

    def process_dependencies(self, dependent_task, dependency_tasks):
        for task in dependency_tasks:
            # ProjectUpdate or InventoryUpdate may be blocked by another of
            # the same type.
            if not self.graph.is_job_blocked(task):
                self.graph.add_job(task)
                if not self.would_exceed_capacity(task):
                    self.start_task(task, [dependent_task])
            else:
                self.graph.add_job(task)

    def process_pending_tasks(self, pending_tasks):
        for task in pending_tasks:
            # Stop processing tasks if we know we are out of capacity
            if self.get_remaining_capacity() <= 0:
                return

            if not self.graph.is_job_blocked(task):
                dependencies = self.generate_dependencies(task)
                self.process_dependencies(task, dependencies)
                
                # Spawning deps might have blocked us
                if not self.graph.is_job_blocked(task):
                    self.graph.add_job(task)
                    if not self.would_exceed_capacity(task):
                        self.start_task(task)
                else:
                    self.graph.add_job(task)

    def process_celery_tasks(self, active_tasks, all_running_sorted_tasks):
        '''
        Rectify tower db <-> celery inconsistent view of jobs state
        '''
        for task in all_running_sorted_tasks:

            if (task['celery_task_id'] not in active_tasks and not hasattr(settings, 'IGNORE_CELERY_INSPECTOR')):
                # NOTE: Pull status again and make sure it didn't finish in 
                #       the meantime?
                # TODO: try catch the getting of the job. The job COULD have been deleted
                task_obj = task.get_full()
                task_obj.status = 'failed'
                task_obj.job_explanation += ' '.join((
                    'Task was marked as running in Tower but was not present in',
                    'Celery, so it has been marked as failed.',
                ))
                task_obj.save()
                connection.on_commit(lambda: task_obj.websocket_emit_status('failed'))

                logger.error("Task %s appears orphaned... marking as failed" % task)


    def calculate_capacity_used(self, tasks):
        self.capacity_used = 0
        for t in tasks:
            self.capacity_used += t.task_impact()

    def would_exceed_capacity(self, task):
        return (task.task_impact() + self.capacity_used > self.capacity_total)

    def consume_capacity(self, task):
        self.capacity_used += task.task_impact()

    def get_remaining_capacity(self):
        return (self.capacity_total - self.capacity_used)

    def process_tasks(self, all_sorted_tasks):
        running_tasks = filter(lambda t: t['status'] == 'running', all_sorted_tasks)
        runnable_tasks = filter(lambda t: t['status'] in ['waiting', 'running'], all_sorted_tasks)

        self.calculate_capacity_used(running_tasks)

        self.process_runnable_tasks(runnable_tasks)

        pending_tasks = filter(lambda t: t['status'] in 'pending', all_sorted_tasks)
        self.process_pending_tasks(pending_tasks)

    def _schedule(self):
        finished_wfjs = []
        all_sorted_tasks = self.get_tasks()
        if len(all_sorted_tasks) > 0:
            latest_project_updates = self.get_latest_project_update_tasks(all_sorted_tasks)
            self.process_latest_project_updates(latest_project_updates)

            latest_inventory_updates = self.get_latest_inventory_update_tasks(all_sorted_tasks)
            self.process_latest_inventory_updates(latest_inventory_updates)
            
            inventory_id_sources = self.get_inventory_source_tasks(all_sorted_tasks)
            self.process_inventory_sources(inventory_id_sources)

            running_workflow_tasks = self.get_running_workflow_jobs()
            finished_wfjs = self.process_finished_workflow_jobs(running_workflow_tasks)

            self.spawn_workflow_graph_jobs(running_workflow_tasks)

            self.process_tasks(all_sorted_tasks)
        return finished_wfjs

    def schedule(self):
        with transaction.atomic():
            # Lock
            try:
                Instance.objects.select_for_update(nowait=True).all()[0]
            except DatabaseError:
                return

            finished_wfjs = self._schedule()

        # Operations whose queries rely on modifications made during the atomic scheduling session
        for wfj in WorkflowJob.objects.filter(id__in=finished_wfjs):
            _send_notification_templates(wfj, 'succeeded' if wfj.status == 'successful' else 'failed')

