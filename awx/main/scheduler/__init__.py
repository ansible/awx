#Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import timedelta
import logging
from sets import Set

# Django
from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError

# AWX
from awx.main.models import * # noqa
#from awx.main.scheduler.dag_simple import SimpleDAG
from awx.main.scheduler.dag_workflow import WorkflowDAG

from awx.main.scheduler.dependency_graph import DependencyGraph
from awx.main.scheduler.partial import (
    JobDict, 
    ProjectUpdateDict, 
    InventoryUpdateDict, 
    ProjectUpdateLatestDict,
)

# Celery
from celery.task.control import inspect

logger = logging.getLogger('awx.main.scheduler')

class Scheduler():
    def __init__(self):
        self.graph = DependencyGraph()
        self.capacity_total = 200
        self.capacity_used = 0

    def _get_tasks_with_status(self, status_list):

        graph_jobs = JobDict.filter_partial(status=status_list)
        '''
        graph_ad_hoc_commands = [ahc for ahc in AdHocCommand.objects.filter(**kv)]
        graph_inventory_updates = [iu for iu in
                                   InventoryUpdate.objects.filter(**kv)]
        '''
        graph_inventory_updates = InventoryUpdateDict.filter_partial(status=status_list)
        graph_project_updates = ProjectUpdateDict.filter_partial(status=status_list)
        '''
        graph_system_jobs = [sj for sj in
                             SystemJob.objects.filter(**kv)]
        graph_workflow_jobs = [wf for wf in
                               WorkflowJob.objects.filter(**kv)]
        all_actions = sorted(graph_jobs + graph_ad_hoc_commands + graph_inventory_updates +
                             graph_project_updates + graph_system_jobs +
                             graph_workflow_jobs,
                             key=lambda task: task.created)
        '''
        all_actions = sorted(graph_jobs + graph_project_updates + graph_inventory_updates,
                             key=lambda task: task['created'])
        return all_actions

    def get_tasks(self):
        RELEVANT_JOBS = ('pending', 'waiting', 'running')
        return self._get_tasks_with_status(RELEVANT_JOBS)

    # TODO: Consider a database query for this logic
    def get_latest_project_update_tasks(self, all_sorted_tasks):
        project_ids = Set()
        for task in all_sorted_tasks:
            if type(task) == JobDict:
                project_ids.add(task['project_id'])

        return ProjectUpdateLatestDict.filter_partial(list(project_ids))

    def get_running_workflow_jobs(self):
        graph_workflow_jobs = [wf for wf in
                               WorkflowJob.objects.filter(status='running')]
        return graph_workflow_jobs

    def spawn_workflow_graph_jobs(self, workflow_jobs):
        # TODO: Consider using transaction.atomic
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
                    job.websocket_emit_status("failed")

                # TODO: should we emit a status on the socket here similar to tasks.py tower_periodic_scheduler() ?
                #emit_websocket_notification('/socket.io/jobs', '', dict(id=))

    # See comment in tasks.py::RunWorkflowJob::run()
    def process_finished_workflow_jobs(self, workflow_jobs):
        for workflow_job in workflow_jobs:
            dag = WorkflowDAG(workflow_job)
            if dag.is_workflow_done():
                # TODO: detect if wfj failed
                if workflow_job._has_failed():
                    workflow_job.status = 'failed'
                else:
                    workflow_job.status = 'successful'
                workflow_job.save()
                workflow_job.websocket_emit_status(workflow_job.status)

    def get_activate_tasks(self):
        inspector = inspect()
        if not hasattr(settings, 'IGNORE_CELERY_INSPECTOR'):
            active_task_queues = inspector.active()
        else:
            logger.warn("Ignoring celery task inspector")
            active_task_queues = None

        active_tasks = []
        if active_task_queues is not None:
            for queue in active_task_queues:
                active_tasks += [at['id'] for at in active_task_queues[queue]]
        else:
            logger.error("Could not communicate with celery!")
            # TODO: Something needs to be done here to signal to the system
            #       as a whole that celery appears to be down.
            if not hasattr(settings, 'CELERY_UNIT_TEST'):
                return None

        return active_tasks

    def start_task(self, task, dependent_tasks=[]):
        from awx.main.tasks import handle_work_error, handle_work_success

        #print("start_task() <%s, %s> with deps %s" % (task.get_job_type_str(), task['id'], dependent_tasks))
            
        # TODO: spawn inventory and project updates                
        task_actual = {
            'type':task.get_job_type_str(),
            'id': task['id'],
        }
        dependencies = [{'type': t.get_job_type_str(), 'id': t['id']} for t in dependent_tasks]
        
        error_handler = handle_work_error.s(subtasks=[task_actual] + dependencies)
        success_handler = handle_work_success.s(task_actual=task_actual)
        
        job_obj = task.get_full()
        job_obj.status = 'waiting'
        job_obj.save()

        #print("For real, starting job <%s, %s>" % (type(job_obj), job_obj.id))
        start_status = job_obj.start(error_callback=error_handler, success_callback=success_handler)
        if not start_status:
            job_obj.status = 'failed'
            if job_obj.job_explanation:
                job_obj.job_explanation += ' '
            job_obj.job_explanation += 'Task failed pre-start check.'
            job_obj.save()
            # TODO: run error handler to fail sub-tasks and send notifications
            return

        self.consume_capacity(task)

    def process_runnable_tasks(self, runnable_tasks):
        for i, task in enumerate(runnable_tasks):
            # TODO: maybe batch process new tasks.
            # Processing a new task individually seems to be expensive
            self.graph.add_job(task)

    def create_project_update(self, task):
        dep = Project.objects.get(id=task['project_id']).create_project_update(launch_type='dependency')

        # TODO: Consider using milliseconds or microseconds
        # Project created 1 seconds behind
        dep.created = task['created'] - timedelta(seconds=1)
        dep.status = 'waiting'
        dep.save()

        project_task = ProjectUpdateDict.get_partial(dep.id)
        #waiting_tasks.insert(waiting_tasks.index(task), dep)

        return project_task

    def generate_dependencies(self, task):
        dependencies = []
        # TODO: What if the project is null ?
        if type(task) is JobDict:
            if task['project__scm_update_on_launch'] is True and \
                    self.graph.should_update_related_project(task):
                project_task = self.create_project_update(task)
                dependencies.append(project_task)
                # Inventory created 2 seconds behind
        return dependencies

    def process_latest_project_updates(self, latest_project_updates):
        for task in latest_project_updates:
            self.graph.add_latest_project_update(task)

    def process_dependencies(self, dependent_task, dependency_tasks):
        for task in dependency_tasks:
            # ProjectUpdate or InventoryUpdate may be blocked by another of
            # the same type.
            if not self.graph.is_job_blocked(task):
                self.graph.add_job(task)
                if not self.would_exceed_capacity(task):
                    #print("process_dependencies() going to run project update <%s, %s>" % (task['id'], task['project_id']))
                    self.start_task(task, [dependent_task])
            else:
                self.graph.add_job(task)

    def process_pending_tasks(self, pending_tasks):
        for task in pending_tasks:

            if not self.graph.is_job_blocked(task):
                #print("process_pending_tasks() generating deps for job <%s, %s, %s>" % (task['id'], task['project_id'], task.model))
                dependencies = self.generate_dependencies(task)
                self.process_dependencies(task, dependencies)
                
                # Spawning deps might have blocked us
                if not self.graph.is_job_blocked(task):
                    self.graph.add_job(task)
                    if not self.would_exceed_capacity(task):
                        #print("Starting the original task <%s, %s>" % (task.get_job_type_str(), task['id']))
                        self.start_task(task)
                else:
                    self.graph.add_job(task)

            # Stop processing tasks if we know we are out of capacity
            if self.get_remaining_capacity() <= 0:
                return

    def fail_inconsistent_running_jobs(self, active_tasks, all_sorted_tasks):
        for i, task in enumerate(all_sorted_tasks):
            if task['status'] != 'running':
                continue

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
                task_obj.websocket_emit_status("failed")

                all_sorted_tasks.pop(i)
                logger.error("Task %s appears orphaned... marking as failed" % task)

    def process_celery_tasks(self, active_tasks, all_sorted_tasks):
        
        '''
        Rectify tower db <-> celery inconsistent view of jobs state
        '''
        # Check running tasks and make sure they are active in celery
        logger.debug("Active celery tasks: " + str(active_tasks))
        all_sorted_tasks = self.fail_inconsistent_running_jobs(active_tasks, 
                                                               all_sorted_tasks)

    def calculate_capacity_used(self, tasks):
        self.capacity_used = 0
        for t in tasks:
            self.capacity_used += t.task_impact()

    def would_exceed_capacity(self, task):
        return (task.task_impact() + self.capacity_used > self.capacity_total)

    def consume_capacity(self, task):
        self.capacity_used += task.task_impact()
        #print("Capacity used %s vs total %s" % (self.capacity_used, self.capacity_total))

    def get_remaining_capacity(self):
        return (self.capacity_total - self.capacity_used)

    def process_tasks(self, all_sorted_tasks):

        # TODO: Process new tasks
        running_tasks = filter(lambda t: t['status'] == 'running', all_sorted_tasks)
        runnable_tasks = filter(lambda t: t['status'] in ['waiting', 'running'], all_sorted_tasks)

        self.calculate_capacity_used(running_tasks)

        self.process_runnable_tasks(runnable_tasks)
        
        pending_tasks = filter(lambda t: t['status'] == 'pending', all_sorted_tasks)
        self.process_pending_tasks(pending_tasks)


        '''
        def do_graph_things():
            # Rebuild graph
            graph = SimpleDAG()
            for task in running_tasks:
                graph.add_node(task)
            #for wait_task in waiting_tasks[:50]:
            for wait_task in waiting_tasks:
                node_dependencies = []
                for node in graph:
                    if wait_task.is_blocked_by(node['node_object']):
                        node_dependencies.append(node['node_object'])
                graph.add_node(wait_task)
                for dependency in node_dependencies:
                    graph.add_edge(wait_task, dependency)
            if settings.DEBUG:
                graph.generate_graphviz_plot()
            return graph
        '''
        #return do_graph_things()

    def _schedule(self):
        all_sorted_tasks = self.get_tasks()
        if len(all_sorted_tasks) > 0:
            #self.process_celery_tasks(active_tasks, all_sorted_tasks)

            latest_project_updates = self.get_latest_project_update_tasks(all_sorted_tasks)
            self.process_latest_project_updates(latest_project_updates)

            self.process_tasks(all_sorted_tasks)

        #print("Finished schedule()")

    def schedule(self):
        with transaction.atomic():
            #t1 = datetime.now()
            # Lock
            try:
                Instance.objects.select_for_update(nowait=True).all()[0]
            except DatabaseError:
                return

            #workflow_jobs = get_running_workflow_jobs()
            #process_finished_workflow_jobs(workflow_jobs)
            #spawn_workflow_graph_jobs(workflow_jobs)

            '''
            Get tasks known by celery
            '''
            '''
            active_tasks = self.get_activate_tasks()
            # Communication with celery failed :(, return
            if active_tasks is None:
                return None
            '''
            self._schedule()

        # Unlock, due to transaction ending
        #t2 = datetime.now()
        #t_diff = t2 - t1
        #print("schedule() time %s" % (t_diff.total_seconds()))



