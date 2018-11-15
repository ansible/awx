
# Python
import copy
from awx.main.models import (
    WorkflowJobTemplateNode,
    WorkflowJobNode,
)

# AWX
from awx.main.scheduler.dag_simple import SimpleDAG


class WorkflowDAG(SimpleDAG):
    def __init__(self, workflow_job=None):
        super(WorkflowDAG, self).__init__()
        if workflow_job:
            self._init_graph(workflow_job)

    def _init_graph(self, workflow_job_or_jt):
        if hasattr(workflow_job_or_jt, 'workflow_job_template_nodes'):
            vals = ['from_workflowjobtemplatenode_id', 'to_workflowjobtemplatenode_id']
            filters = {
                'from_workflowjobtemplatenode__workflow_job_template_id': workflow_job_or_jt.id
            }
            workflow_nodes = workflow_job_or_jt.workflow_job_template_nodes
            success_nodes = WorkflowJobTemplateNode.success_nodes.through.objects.filter(**filters).values_list(*vals)
            failure_nodes = WorkflowJobTemplateNode.failure_nodes.through.objects.filter(**filters).values_list(*vals)
            always_nodes = WorkflowJobTemplateNode.always_nodes.through.objects.filter(**filters).values_list(*vals)
        elif hasattr(workflow_job_or_jt, 'workflow_job_nodes'):
            vals = ['from_workflowjobnode_id', 'to_workflowjobnode_id']
            filters = {
                'from_workflowjobnode__workflow_job_id': workflow_job_or_jt.id
            }
            workflow_nodes = workflow_job_or_jt.workflow_job_nodes
            success_nodes = WorkflowJobNode.success_nodes.through.objects.filter(**filters).values_list(*vals)
            failure_nodes = WorkflowJobNode.failure_nodes.through.objects.filter(**filters).values_list(*vals)
            always_nodes = WorkflowJobNode.always_nodes.through.objects.filter(**filters).values_list(*vals)
        else:
            raise RuntimeError("Unexpected object {} {}".format(type(workflow_job_or_jt), workflow_job_or_jt))

        wfn_by_id = dict()

        for workflow_node in workflow_nodes.all():
            wfn_by_id[workflow_node.id] = workflow_node
            self.add_node(workflow_node)

        for edge in success_nodes:
            self.add_edge(wfn_by_id[edge[0]], wfn_by_id[edge[1]], 'success_nodes')
        for edge in failure_nodes:
            self.add_edge(wfn_by_id[edge[0]], wfn_by_id[edge[1]], 'failure_nodes')
        for edge in always_nodes:
            self.add_edge(wfn_by_id[edge[0]], wfn_by_id[edge[1]], 'always_nodes')

    r'''
    Determine if all, relevant, parents node are finished.
    Relevant parents are parents that are marked do_not_run False.

    :param node:     a node entry from SimpleDag.nodes (i.e. a dict with property ['node_object']

    Return a boolean
    '''
    def _are_relevant_parents_finished(self, node):
        obj = node['node_object']
        parent_nodes = [p['node_object'] for p in self.get_dependents(obj)]
        for p in parent_nodes:
            if p.do_not_run is True:
                continue

            # Node might run a job
            if p.do_not_run is False and not p.job:
                return False

            # Node decidedly got a job; check if job is done
            if p.job and p.job.status not in ['successful', 'failed', 'error']:
                return False
        return True

    def bfs_nodes_to_run(self):
        nodes = self.get_root_nodes()
        nodes_found = []
        node_ids_visited = set()

        for index, n in enumerate(nodes):
            obj = n['node_object']
            if obj.id in node_ids_visited:
                continue
            node_ids_visited.add(obj.id)

            if obj.do_not_run is True:
                continue

            if obj.job:
                if obj.job.status in ['failed', 'error', 'canceled']:
                    nodes.extend(self.get_dependencies(obj, 'failure_nodes') +
                                 self.get_dependencies(obj, 'always_nodes'))
                elif obj.job.status == 'successful':
                    nodes.extend(self.get_dependencies(obj, 'success_nodes') +
                                 self.get_dependencies(obj, 'always_nodes'))
            else:
                if self._are_relevant_parents_finished(n):
                    nodes_found.append(n)
        return [n['node_object'] for n in nodes_found]

    def cancel_node_jobs(self):
        cancel_finished = True
        for n in self.nodes:
            obj = n['node_object']
            job = obj.job

            if not job:
                continue
            elif job.can_cancel:
                cancel_finished = False
                job.cancel()
        return cancel_finished

    def is_workflow_done(self):
        for node in self.nodes:
            obj = node['node_object']
            if obj.do_not_run is False and not obj.job:
                return False
            elif obj.job and obj.job.status not in ['successful', 'failed', 'canceled', 'error']:
                return False
        return True

    def has_workflow_failed(self):
        failed_nodes = []
        for node in self.nodes:
            obj = node['node_object']
            if obj.job and obj.job.status in ['failed', 'canceled', 'error']:
                failed_nodes.append(node)
        for node in failed_nodes:
            obj = node['node_object']
            if (len(self.get_dependencies(obj, 'failure_nodes')) +
                    len(self.get_dependencies(obj, 'always_nodes'))) == 0:
                return True
        return False

    r'''
    Determine if all nodes have been decided on being marked do_not_run.
    Nodes that are do_not_run False may become do_not_run True in the future.
    We know a do_not_run False node will NOT be marked do_not_run True if there
    is a job run for that node.

    :param workflow_nodes:     list of workflow_nodes

    Return a boolean
    '''
    def _are_all_nodes_dnr_decided(self, workflow_nodes):
        for n in workflow_nodes:
            if n.do_not_run is False and not n.job:
                return False
        return True


    r'''
    Determine if a node (1) is ready to be marked do_not_run and (2) should
    be marked do_not_run.

    :param node:             SimpleDAG internal node
    :param parent_nodes:     list of workflow_nodes

    Return a boolean
    '''
    def _should_mark_node_dnr(self, node, parent_nodes):
        for p in parent_nodes:
            if p.job:
                if p.job.status == 'successful':
                    if node in (self.get_dependencies(p, 'success_nodes') +
                                self.get_dependencies(p, 'always_nodes')):
                        return False
                elif p.job.status in ['failed', 'error', 'canceled']:
                    if node in (self.get_dependencies(p, 'failure_nodes') +
                                self.get_dependencies(p, 'always_nodes')):
                        return False
                else:
                    return False
            else:
                return False
        return True

    def mark_dnr_nodes(self):
        root_nodes = self.get_root_nodes()
        nodes = copy.copy(root_nodes)
        nodes_marked_do_not_run = []
        node_ids_visited = set()

        for index, n in enumerate(nodes):
            obj = n['node_object']
            if obj.id in node_ids_visited:
                continue
            node_ids_visited.add(obj.id)

            if obj.do_not_run is False and not obj.job and n not in root_nodes:
                parent_nodes = filter(lambda n: not n.do_not_run,
                                      [p['node_object'] for p in self.get_dependents(obj)])
                if self._are_all_nodes_dnr_decided(parent_nodes):
                    if self._should_mark_node_dnr(n, parent_nodes):
                        obj.do_not_run = True
                        nodes_marked_do_not_run.append(n)

            nodes.extend(self.get_dependencies(obj, 'success_nodes') +
                         self.get_dependencies(obj, 'failure_nodes') +
                         self.get_dependencies(obj, 'always_nodes'))
        return [n['node_object'] for n in nodes_marked_do_not_run]
