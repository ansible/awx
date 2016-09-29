#Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import datetime
import logging

# Django
from django.conf import settings
from django.db import transaction

# AWX
from awx.main.models import * # noqa
from awx.main.utils import get_system_task_capacity
from awx.main.scheduler.dag_simple import SimpleDAG
from awx.main.scheduler.dag_workflow import WorkflowDAG

# Celery
from celery.task.control import inspect

logger = logging.getLogger('awx.main.scheduler')

def get_tasks():
    """Fetch all Tower tasks that are relevant to the task management
    system.
    """
    RELEVANT_JOBS = ('pending', 'waiting', 'running')
    # TODO: Replace this when we can grab all objects in a sane way.
    graph_jobs = [j for j in Job.objects.filter(status__in=RELEVANT_JOBS)]
    graph_ad_hoc_commands = [ahc for ahc in AdHocCommand.objects.filter(status__in=RELEVANT_JOBS)]
    graph_inventory_updates = [iu for iu in
                               InventoryUpdate.objects.filter(status__in=RELEVANT_JOBS)]
    graph_project_updates = [pu for pu in
                             ProjectUpdate.objects.filter(status__in=RELEVANT_JOBS)]
    graph_system_jobs = [sj for sj in
                         SystemJob.objects.filter(status__in=RELEVANT_JOBS)]
    graph_workflow_jobs = [wf for wf in
                           WorkflowJob.objects.filter(status__in=RELEVANT_JOBS)]
    all_actions = sorted(graph_jobs + graph_ad_hoc_commands + graph_inventory_updates +
                         graph_project_updates + graph_system_jobs +
                         graph_workflow_jobs,
                         key=lambda task: task.created)
    return all_actions

def get_running_workflow_jobs():
    graph_workflow_jobs = [wf for wf in
                           WorkflowJob.objects.filter(status='running')]
    return graph_workflow_jobs

def spawn_workflow_graph_jobs(workflow_jobs):
    # TODO: Consider using transaction.atomic
    for workflow_job in workflow_jobs:
        dag = WorkflowDAG(workflow_job)
        spawn_nodes = dag.bfs_nodes_to_run()
        for spawn_node in spawn_nodes:
            # TODO: Inject job template template params as kwargs.
            # Make sure to take into account extra_vars merge logic
            kv = {}
            job = spawn_node.unified_job_template.create_unified_job(**kv)
            spawn_node.job = job
            spawn_node.save()
            can_start = job.signal_start(**kv)
            if not can_start:
                job.status = 'failed'
                job.job_explanation = "Workflow job could not start because it was not in the right state or required manual credentials"
                job.save(update_fields=['status', 'job_explanation'])
                job.socketio_emit_status("failed")

            # TODO: should we emit a status on the socket here similar to tasks.py tower_periodic_scheduler() ?
            #emit_websocket_notification('/socket.io/jobs', '', dict(id=))

# See comment in tasks.py::RunWorkflowJob::run()
def process_finished_workflow_jobs(workflow_jobs):
    for workflow_job in workflow_jobs:
        dag = WorkflowDAG(workflow_job)
        if dag.is_workflow_done():
            with transaction.atomic():
                # TODO: detect if wfj failed
                workflow_job.status = 'completed'
                workflow_job.save()
                workflow_job.socketio_emit_status('completed')

def rebuild_graph():
    """Regenerate the task graph by refreshing known tasks from Tower, purging
    orphaned running tasks, and creating dependencies for new tasks before
    generating directed edge relationships between those tasks.
    """
    '''
    # Sanity check: Only do this on the primary node.
    if Instance.objects.my_role() == 'secondary':
        return None
    '''

    inspector = inspect()
    if not hasattr(settings, 'IGNORE_CELERY_INSPECTOR'):
        active_task_queues = inspector.active()
    else:
        logger.warn("Ignoring celery task inspector")
        active_task_queues = None

    all_sorted_tasks = get_tasks()
    if not len(all_sorted_tasks):
        return None

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

    running_tasks = filter(lambda t: t.status == 'running', all_sorted_tasks)
    running_celery_tasks = filter(lambda t: type(t) != WorkflowJob, running_tasks)
    waiting_tasks = filter(lambda t: t.status != 'running', all_sorted_tasks)
    new_tasks = filter(lambda t: t.status == 'pending', all_sorted_tasks)

    # Check running tasks and make sure they are active in celery
    logger.debug("Active celery tasks: " + str(active_tasks))
    for task in list(running_celery_tasks):
        if (task.celery_task_id not in active_tasks and not hasattr(settings, 'IGNORE_CELERY_INSPECTOR')):
            # NOTE: Pull status again and make sure it didn't finish in 
            #       the meantime?
            task.status = 'failed'
            task.job_explanation += ' '.join((
                'Task was marked as running in Tower but was not present in',
                'Celery, so it has been marked as failed.',
            ))
            task.save()
            task.socketio_emit_status("failed")
            running_tasks.pop(task)
            logger.error("Task %s appears orphaned... marking as failed" % task)

    # Create and process dependencies for new tasks
    for task in new_tasks:
        logger.debug("Checking dependencies for: %s" % str(task))
        try:
            task_dependencies = task.generate_dependencies(running_tasks + waiting_tasks)
        except Exception, e:
            logger.error("Failed processing dependencies for {}: {}".format(task, e))
            task.status = 'failed'
            task.job_explanation += 'Task failed to generate dependencies: {}'.format(e)
            task.save()
            task.socketio_emit_status("failed")
            continue
        logger.debug("New dependencies: %s" % str(task_dependencies))
        for dep in task_dependencies:
            # We recalculate the created time for the moment to ensure the
            # dependencies are always sorted in the right order relative to
            # the dependent task.
            time_delt = len(task_dependencies) - task_dependencies.index(dep)
            dep.created = task.created - datetime.timedelta(seconds=1 + time_delt)
            dep.status = 'waiting'
            dep.save()
            waiting_tasks.insert(waiting_tasks.index(task), dep)
        if not hasattr(settings, 'UNIT_TEST_IGNORE_TASK_WAIT'):
            task.status = 'waiting'
            task.save()

    # Rebuild graph
    graph = SimpleDAG()
    for task in running_tasks:
        graph.add_node(task)
    for wait_task in waiting_tasks[:50]:
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

def process_graph(graph, task_capacity):
    """Given a task dependency graph, start and manage tasks given their
    priority and weight.
    """
    from awx.main.tasks import handle_work_error, handle_work_success

    leaf_nodes = graph.get_leaf_nodes()
    running_nodes = filter(lambda x: x['node_object'].status == 'running', leaf_nodes)
    running_impact = sum([t['node_object'].task_impact for t in running_nodes])
    ready_nodes = filter(lambda x: x['node_object'].status != 'running', leaf_nodes)
    remaining_volume = task_capacity - running_impact
    logger.info('Running Nodes: %s; Capacity: %s; Running Impact: %s; '
                'Remaining Capacity: %s' %
                (str(running_nodes), str(task_capacity),
                 str(running_impact), str(remaining_volume)))
    logger.info("Ready Nodes: %s" % str(ready_nodes))
    for task_node in ready_nodes:
        node_obj = task_node['node_object']
        # NOTE: This could be used to pass metadata through the task system
        # node_args = task_node['metadata']
        impact = node_obj.task_impact
        if impact <= remaining_volume or running_impact == 0:
            node_dependencies = graph.get_dependents(node_obj)
            # Allow other tasks to continue if a job fails, even if they are
            # other jobs.

            node_type = graph.get_node_type(node_obj)
            if node_type == 'job':
                # clear dependencies because a job can block (not necessarily 
                # depend) on other jobs that share the same job template
                node_dependencies = []

            # Make the workflow_job look like it's started by setting status to
            # running, but don't make a celery Task for it.
            # Introduce jobs from the workflow so they are candidates to run.
            # Call process_graph() again to allow choosing for run, the
            # created candidate jobs.
            elif node_type == 'workflow_job':
                node_obj.start()
                spawn_workflow_graph_jobs([node_obj])
                return process_graph(graph, task_capacity)
            
            dependent_nodes = [{'type': graph.get_node_type(node_obj), 'id': node_obj.id}] + \
                              [{'type': graph.get_node_type(n['node_object']),
                                'id': n['node_object'].id} for n in node_dependencies]
            error_handler = handle_work_error.s(subtasks=dependent_nodes)
            success_handler = handle_work_success.s(task_actual={'type': graph.get_node_type(node_obj),
                                                                 'id': node_obj.id})
            with transaction.atomic():
                start_status = node_obj.start(error_callback=error_handler, success_callback=success_handler)
                if not start_status:
                    node_obj.status = 'failed'
                    if node_obj.job_explanation:
                        node_obj.job_explanation += ' '
                    node_obj.job_explanation += 'Task failed pre-start check.'
                    node_obj.save()
                    continue
            remaining_volume -= impact
            running_impact += impact
            logger.info('Started Node: %s (capacity hit: %s) '
                        'Remaining Capacity: %s' %
                        (str(node_obj), str(impact), str(remaining_volume)))

def schedule():
    with transaction.atomic():
        # Lock
        Instance.objects.select_for_update().all()[0]

        task_capacity = get_system_task_capacity()

        workflow_jobs = get_running_workflow_jobs()
        process_finished_workflow_jobs(workflow_jobs)
        spawn_workflow_graph_jobs(workflow_jobs)

        graph = rebuild_graph()
        if graph:
            process_graph(graph, task_capacity)

        # Unlock, due to transaction ending
