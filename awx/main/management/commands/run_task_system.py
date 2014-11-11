#Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

# Python
import os
import datetime
import logging
import json
import signal
import time
from optparse import make_option
from multiprocessing import Process

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction, DatabaseError
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, is_aware, make_aware
from django.utils.tzinfo import FixedOffset

# AWX
from awx.main.models import *
from awx.main.queue import FifoQueue
from awx.main.tasks import handle_work_error
from awx.main.utils import get_system_task_capacity, decrypt_field

# Celery
from celery.task.control import inspect


queue = FifoQueue('tower_task_manager')


def print_log(message):
    print("[%s] %s" % (now().isoformat(), message))


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
            elif type(obj) == InventoryUpdate:
                type_str = "Inventory"
            elif type(obj) == ProjectUpdate:
                type_str = "Project"
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
        for from_node, to_node in self.edges:
            doc += "%s -> %s;\n" % (
                short_string_obj(self.nodes[from_node]['node_object']),
                short_string_obj(self.nodes[to_node]['node_object']),
            )
        doc += "}\n"
        gv_file = open('/tmp/graph.gv', 'w')
        gv_file.write(doc)
        gv_file.close()

    def add_node(self, obj, metadata=None):
        if self.find_ord(obj) is None:
            self.nodes.append(dict(node_object=obj, metadata=metadata))

    def add_edge(self, from_obj, to_obj):
        from_obj_ord = self.find_ord(from_obj)
        to_obj_ord = self.find_ord(to_obj)
        if from_obj_ord is None or to_obj_ord is None:
            raise LookupError("Object not found")
        self.edges.append((from_obj_ord, to_obj_ord))

    def add_edges(self, edgelist):
        for edge_pair in edgelist:
            self.add_edge(edge_pair[0], edge_pair[1])

    def find_ord(self, obj):
        for idx in range(len(self.nodes)):
            if obj == self.nodes[idx]['node_object']:
                return idx
        return None

    def get_node_type(self, obj):
        if type(obj) == Job:
            return "job"
        elif type(obj) == InventoryUpdate:
            return "inventory_update"
        elif type(obj) == ProjectUpdate:
            return "project_update"
        return "unknown"

    def get_dependencies(self, obj):
        antecedents = []
        this_ord = self.find_ord(obj)
        for node, dep in self.edges:
            if node == this_ord:
                antecedents.append(self.nodes[dep])
        return antecedents

    def get_dependents(self, obj):
        decendents = []
        this_ord = self.find_ord(obj)
        for node, dep in self.edges:
            if dep == this_ord:
                decendents.append(self.nodes[node])
        return decendents

    def get_leaf_nodes(self):
        leafs = []
        for n in self.nodes:
            if len(self.get_dependencies(n['node_object'])) < 1:
                leafs.append(n)
        return leafs

def get_tasks():
    """Fetch all Tower tasks that are relevant to the task management
    system.
    """
    RELEVANT_JOBS = ('pending', 'waiting', 'running')
    # TODO: Replace this when we can grab all objects in a sane way.
    graph_jobs = [j for j in Job.objects.filter(status__in=RELEVANT_JOBS)]
    graph_inventory_updates = [iu for iu in
                InventoryUpdate.objects.filter(status__in=RELEVANT_JOBS)]
    graph_project_updates = [pu for pu in
                ProjectUpdate.objects.filter(status__in=RELEVANT_JOBS)]
    graph_system_jobs = [sj for sj in
                SystemJob.objects.filter(status__in=RELEVANT_JOBS)]
    all_actions = sorted(graph_jobs + graph_inventory_updates +
                         graph_project_updates + graph_system_jobs,
                         key=lambda task: task.created)
    return all_actions

def rebuild_graph(message):
    """Regenerate the task graph by refreshing known tasks from Tower, purging
    orphaned running tasks, and creating dependencies for new tasks before
    generating directed edge relationships between those tasks.
    """
    inspector = inspect()
    if not hasattr(settings, 'IGNORE_CELERY_INSPECTOR'):
        active_task_queues = inspector.active()
    else:
        print_log("Ignoring celery task inspector")
        active_task_queues = None

    all_sorted_tasks = get_tasks()
    if not len(all_sorted_tasks):
        return None

    active_tasks = []
    if active_task_queues is not None:
        for queue in active_task_queues:
            active_tasks += [at['id'] for at in active_task_queues[queue]]
    else:
        if settings.DEBUG:
            print_log("Could not communicate with celery!")
            # TODO: Something needs to be done here to signal to the system
            #       as a whole that celery appears to be down.
        if not hasattr(settings, 'CELERY_UNIT_TEST'):
            return None
    running_tasks = filter(lambda t: t.status == 'running', all_sorted_tasks)
    waiting_tasks = filter(lambda t: t.status != 'running', all_sorted_tasks)
    new_tasks = filter(lambda t: t.status == 'pending', all_sorted_tasks)

    # Check running tasks and make sure they are active in celery
    print_log("Active celery tasks: " + str(active_tasks))
    for task in list(running_tasks):
        if (task.celery_task_id not in active_tasks and
                    not hasattr(settings, 'IGNORE_CELERY_INSPECTOR')):
            # NOTE: Pull status again and make sure it didn't finish in 
            #       the meantime?
            task.status = 'failed'
            task.job_explanation += ''.join((
                'Task was marked as running in Tower but was not present in',
                'Celery so it has been marked as failed',
            ))
            task.save()
            task.socketio_emit_status("failed")
            running_tasks.pop(running_tasks.index(task))
            print_log("Task %s appears orphaned... marking as failed" % task)

    # Create and process dependencies for new tasks
    for task in new_tasks:
        print_log("Checking dependencies for: %s" % str(task))
        task_dependencies = task.generate_dependencies(running_tasks + waiting_tasks) #TODO: other 'new' tasks? Need to investigate this scenario
        print_log("New dependencies: %s" % str(task_dependencies))
        for dep in task_dependencies:
            # We recalculate the created time for the moment to ensure the
            # dependencies are always sorted in the right order relative to
            # the dependent task.
            time_delt = len(task_dependencies) - task_dependencies.index(dep)
            dep.created = task.created - datetime.timedelta(seconds=1+time_delt)
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

def process_graph(graph, task_capacity):
    """Given a task dependency graph, start and manage tasks given their
    priority and weight.
    """
    leaf_nodes = graph.get_leaf_nodes()
    running_nodes = filter(lambda x: x['node_object'].status == 'running', leaf_nodes)
    running_impact = sum([t['node_object'].task_impact for t in running_nodes])
    ready_nodes = filter(lambda x: x['node_object'].status != 'running', leaf_nodes)
    remaining_volume = task_capacity - running_impact
    print_log('Running Nodes: %s; Capacity: %s; Running Impact: %s; '
             'Remaining Capacity: %s' %
             (str(running_nodes), str(task_capacity),
              str(running_impact), str(remaining_volume)))
    print_log("Ready Nodes: %s" % str(ready_nodes))
    for task_node in ready_nodes:
        node_obj = task_node['node_object']
        node_args = task_node['metadata']
        impact = node_obj.task_impact
        node_is_job = graph.get_node_type(node_obj) == 'job'
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
            start_status = node_obj.start(error_callback=error_handler)
            if not start_status:
                node_obj.status = 'failed'
                if node_obj.job_explanation:
                    node_obj.job_explanation += ' '
                node_obj.job_explanation += 'Task failed pre-start check.'
                node_obj.save()
                # TODO: Run error handler
                continue
            remaining_volume -= impact
            running_impact += impact
            print_log('Started Node: %s (capacity hit: %s) '
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
    while True:
        # Pop a message off the queue.
        # (If the queue is empty, None will be returned.)
        message = queue.pop()

        # Sanity check: If we got no message back, sleep and continue.
        if message is None:
            time.sleep(0.1)
            continue

        # Parse out the message appropriately, rebuilding our graph if
        # appropriate.
        if (datetime.datetime.now() - last_rebuild).seconds > 10:
            if 'pause' in message:
                print_log("Pause command received: %s" % str(message))
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

    def init_logging(self):
        log_levels = dict(enumerate([logging.ERROR, logging.INFO,
                                     logging.DEBUG, 0]))
        self.logger = logging.getLogger('awx.main.commands.run_task_system')
        self.logger.setLevel(log_levels.get(self.verbosity, 0))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.init_logging()
        try:
            run_taskmanager()
        except KeyboardInterrupt:
            pass
