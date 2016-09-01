#Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import os
import datetime
import logging
import signal
import time

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand

# AWX
from awx.main.models import * # noqa
from awx.main.queue import FifoQueue
from awx.main.tasks import handle_work_error, handle_work_success
from awx.main.utils import get_system_task_capacity

# Celery
from celery.task.control import inspect

logger = logging.getLogger('awx.main.commands.run_task_system')

queue = FifoQueue('tower_task_manager')

class SimpleDAG(object):
    ''' A simple implementation of a directed acyclic graph '''

    def __init__(self):
        self.nodes = []
        self.edges = []

    def __contains__(self, obj):
        for node in self.nodes:
            if node['node_object'] == obj:
                return True
        return False

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        return self.nodes.__iter__()

    def generate_graphviz_plot(self):
        def short_string_obj(obj):
            if type(obj) == Job:
                type_str = "Job"
            if type(obj) == AdHocCommand:
                type_str = "AdHocCommand"
            elif type(obj) == InventoryUpdate:
                type_str = "Inventory"
            elif type(obj) == ProjectUpdate:
                type_str = "Project"
            elif type(obj) == WorkflowJob:
                type_str = "Workflow"
            else:
                type_str = "Unknown"
            type_str += "%s" % str(obj.id)
            return type_str

        doc = """
        digraph g {
        rankdir = LR
        """
        for n in self.nodes:
            doc += "%s [color = %s]\n" % (
                short_string_obj(n['node_object']),
                "red" if n['node_object'].status == 'running' else "black",
            )
        for from_node, to_node, label in self.edges:
            doc += "%s -> %s [ label=\"%s\" ];\n" % (
                short_string_obj(self.nodes[from_node]['node_object']),
                short_string_obj(self.nodes[to_node]['node_object']),
                label,
            )
        doc += "}\n"
        gv_file = open('/tmp/graph.gv', 'w')
        gv_file.write(doc)
        gv_file.close()

    def add_node(self, obj, metadata=None):
        if self.find_ord(obj) is None:
            self.nodes.append(dict(node_object=obj, metadata=metadata))

    def add_edge(self, from_obj, to_obj, label=None):
        from_obj_ord = self.find_ord(from_obj)
        to_obj_ord = self.find_ord(to_obj)
        if from_obj_ord is None or to_obj_ord is None:
            raise LookupError("Object not found")
        self.edges.append((from_obj_ord, to_obj_ord, label))

    def add_edges(self, edgelist):
        for edge_pair in edgelist:
            self.add_edge(edge_pair[0], edge_pair[1], edge_pair[2])

    def find_ord(self, obj):
        for idx in range(len(self.nodes)):
            if obj == self.nodes[idx]['node_object']:
                return idx
        return None

    def get_node_type(self, obj):
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

    def get_dependencies(self, obj, label=None):
        antecedents = []
        this_ord = self.find_ord(obj)
        for node, dep, lbl in self.edges:
            if label:
                if node == this_ord and lbl == label:
                    antecedents.append(self.nodes[dep])
            else:
                if node == this_ord:
                    antecedents.append(self.nodes[dep])
        return antecedents

    def get_dependents(self, obj, label=None):
        decendents = []
        this_ord = self.find_ord(obj)
        for node, dep, lbl in self.edges:
            if label:
                if dep == this_ord and lbl == label:
                    decendents.append(self.nodes[node])
            else:
                if dep == this_ord:
                    decendents.append(self.nodes[node])
        return decendents

    def get_leaf_nodes(self):
        leafs = []
        for n in self.nodes:
            if len(self.get_dependencies(n['node_object'])) < 1:
                leafs.append(n)
        return leafs

    def get_root_nodes(self):
        roots = []
        for n in self.nodes:
            if len(self.get_dependents(n['node_object'])) < 1:
                roots.append(n)
        return roots

class WorkflowDAG(SimpleDAG):
    def __init__(self, workflow_job=None):
        super(WorkflowDAG, self).__init__()
        if workflow_job:
            self._init_graph(workflow_job)

    def _init_graph(self, workflow_job):
        workflow_nodes = workflow_job.workflow_job_nodes.all()
        for workflow_node in workflow_nodes:
            self.add_node(workflow_node)

        for node_type in ['success_nodes', 'failure_nodes', 'always_nodes']:
            for workflow_node in workflow_nodes:
                related_nodes = getattr(workflow_node, node_type).all()
                for related_node in related_nodes:
                    self.add_edge(workflow_node, related_node, node_type)

    def bfs_nodes_to_run(self):
        root_nodes = self.get_root_nodes()
        nodes = root_nodes
        nodes_found = []

        for index, n in enumerate(nodes):
            obj = n['node_object']
            job = obj.job
            print("\t\tExamining node %s job %s" % (obj, job))

            if not job:
                print("\t\tNo job for node %s" % obj)
                nodes_found.append(n)
            # Job is about to run or is running. Hold our horses and wait for
            # the job to finish. We can't proceed down the graph path until we
            # have the job result.
            elif job.status not in ['failed', 'error', 'successful']:
                print("\t\tJob status not 'failed' 'error' nor 'successful' %s" % job.status)
                continue
            elif job.status in ['failed', 'error']:
                print("\t\tJob status is failed or error %s" % job.status)
                children_failed = self.get_dependencies(obj, 'failure_nodes')
                children_always = self.get_dependencies(obj, 'always_nodes')
                children_all = children_failed + children_always
                nodes.extend(children_all)
            elif job.status in ['successful']:
                print("\t\tJob status is successful %s" % job.status)
                children_success = self.get_dependencies(obj, 'success_nodes')
                nodes.extend(children_success)
            else:
                logger.warn("Incorrect graph structure")
        return [n['node_object'] for n in nodes_found]

    def is_workflow_done(self):
        root_nodes = self.get_root_nodes()
        nodes = root_nodes

        for index, n in enumerate(nodes):
            obj = n['node_object']
            job = obj.job

            if not job:
                return False
            # Job is about to run or is running. Hold our horses and wait for
            # the job to finish. We can't proceed down the graph path until we
            # have the job result.
            elif job.status not in ['failed', 'error', 'successful']:
                return False
            elif job.status in ['failed', 'error']:
                children_failed = self.get_dependencies(obj, 'failure_nodes')
                children_always = self.get_dependencies(obj, 'always_nodes')
                children_all = children_failed + children_always
                nodes.extend(children_all)
            elif job.status in ['successful']:
                children_success = self.get_dependencies(obj, 'success_nodes')
                nodes.extend(children_success)
            else:
                logger.warn("Incorrect graph structure")
        return True

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

def do_spawn_workflow_jobs():
    workflow_jobs = get_running_workflow_jobs()
    print("Set of workflow jobs to process %s" % workflow_jobs)
    for workflow_job in workflow_jobs:
        print("Building the dag")
        dag = WorkflowDAG(workflow_job)
        print("Imported the workflow job dag")
        for n in dag.nodes:
            print("\tWorkflow dag node %s" % n)
        for f, to, label in dag.edges:
            print("\tWorkflow dag edge <%s,%s,%s>" % (f, to, label))
        spawn_nodes = dag.bfs_nodes_to_run()
        for spawn_node in spawn_nodes:
            print("Spawning job %s" % spawn_node)
            # TODO: Inject job template template params as kwargs
            kv = {}
            job = spawn_node.unified_job_template.create_unified_job(**kv)
            print("Started new job %s" % job.id)
            spawn_node.job = job
            spawn_node.save()
            result = job.signal_start(**kv)

def rebuild_graph(message):
    """Regenerate the task graph by refreshing known tasks from Tower, purging
    orphaned running tasks, and creating dependencies for new tasks before
    generating directed edge relationships between those tasks.
    """
    # Sanity check: Only do this on the primary node.
    if Instance.objects.my_role() == 'secondary':
        return None

    inspector = inspect()
    if not hasattr(settings, 'IGNORE_CELERY_INSPECTOR'):
        active_task_queues = inspector.active()
    else:
        logger.warn("Ignoring celery task inspector")
        active_task_queues = None

    do_spawn_workflow_jobs()

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
    waiting_tasks = filter(lambda t: t.status != 'running', all_sorted_tasks)
    new_tasks = filter(lambda t: t.status == 'pending', all_sorted_tasks)

    # Check running tasks and make sure they are active in celery
    logger.debug("Active celery tasks: " + str(active_tasks))
    for task in list(running_tasks):
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
            running_tasks.pop(running_tasks.index(task))
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
            if graph.get_node_type(node_obj) == 'job':
                node_dependencies = []
            dependent_nodes = [{'type': graph.get_node_type(node_obj), 'id': node_obj.id}] + \
                              [{'type': graph.get_node_type(n['node_object']),
                                'id': n['node_object'].id} for n in node_dependencies]
            error_handler = handle_work_error.s(subtasks=dependent_nodes)
            success_handler = handle_work_success.s(task_actual={'type': graph.get_node_type(node_obj),
                                                                 'id': node_obj.id})
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

def run_taskmanager():
    """Receive task start and finish signals to rebuild a dependency graph
    and manage the actual running of tasks.
    """
    def shutdown_handler():
        def _handler(signum, frame):
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
        return _handler
    signal.signal(signal.SIGINT, shutdown_handler())
    signal.signal(signal.SIGTERM, shutdown_handler())
    paused = False
    task_capacity = get_system_task_capacity()
    last_rebuild = datetime.datetime.fromtimestamp(0)

    # Attempt to pull messages off of the task system queue into perpetuity.
    #
    # A quick explanation of what is happening here:
    # The popping messages off the queue bit is something of a sham. We remove
    # the messages from the queue and then immediately throw them away. The
    # `rebuild_graph` function, while it takes the message as an argument,
    # ignores it.
    #
    # What actually happens is that we just check the database every 10 seconds
    # to see what the task dependency graph looks like, and go do that. This
    # is the job of the `rebuild_graph` function.
    #
    # There is some placeholder here: we may choose to actually use the message
    # in the future.
    while True:
        # Pop a message off the queue.
        # (If the queue is empty, None will be returned.)
        message = queue.pop()

        # Parse out the message appropriately, rebuilding our graph if
        # appropriate.
        if (datetime.datetime.now() - last_rebuild).seconds > 10:
            if message is not None and 'pause' in message:
                logger.info("Pause command received: %s" % str(message))
                paused = message['pause']
            graph = rebuild_graph(message)
            if not paused and graph is not None:
                process_graph(graph, task_capacity)
            last_rebuild = datetime.datetime.now()
        time.sleep(0.1)


class Command(NoArgsCommand):
    """Tower Task Management System
    This daemon is designed to reside between our tasks and celery and
    provide a mechanism for understanding the relationship between those tasks
    and their dependencies.

    It also actively prevents situations in which Tower can get blocked
    because it doesn't have an understanding of what is progressing through
    celery.
    """
    help = 'Launch the Tower task management system'

    def handle_noargs(self, **options):
        try:
            run_taskmanager()
        except KeyboardInterrupt:
            pass
