
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text

# Python
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

    def _are_relevant_parents_finished(self, node):
        obj = node['node_object']
        parent_nodes = [p['node_object'] for p in self.get_parents(obj)]
        for p in parent_nodes:
            if p.do_not_run is True:
                continue
            elif p.unified_job_template is None:
                continue
            # do_not_run is False, node might still run a job and thus blocks children
            elif not p.job:
                return False
            # Node decidedly got a job; check if job is done
            elif p.job and p.job.status not in ['successful', 'failed', 'error', 'canceled']:
                return False
        return True

    def _all_parents_met_convergence_criteria(self, node):
        # This function takes any node and checks that all it's parents have met their criteria to run the child.
        # This returns a boolean and is really only useful if the node is an ALL convergence node and is
        # intended to be used in conjuction with the node property `all_parents_must_converge`
        obj = node['node_object']
        parent_nodes = [p['node_object'] for p in self.get_parents(obj)]
        for p in parent_nodes:
            #node has a status
            if p.job and p.job.status in ["successful", "failed"]:
                if p.job and p.job.status == "successful":
                    status = "success_nodes"
                elif p.job and p.job.status == "failed":
                    status = "failure_nodes"
                #check that the nodes status matches either a pathway of the same status or is an always path.
                if (p not in [node['node_object'] for node in self.get_parents(obj, status)] and
                        p not in [node['node_object'] for node in self.get_parents(obj, "always_nodes")]):
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
            elif obj.job:
                if obj.job.status in ['failed', 'error', 'canceled']:
                    nodes.extend(self.get_children(obj, 'failure_nodes') +
                                 self.get_children(obj, 'always_nodes'))
                elif obj.job.status == 'successful':
                    nodes.extend(self.get_children(obj, 'success_nodes') +
                                 self.get_children(obj, 'always_nodes'))
            elif obj.unified_job_template is None:
                nodes.extend(self.get_children(obj, 'failure_nodes') +
                             self.get_children(obj, 'always_nodes'))
            else:
                # This catches root nodes or ANY convergence nodes
                if not obj.all_parents_must_converge and self._are_relevant_parents_finished(n):
                    nodes_found.append(n)
                # This catches ALL convergence nodes
                elif obj.all_parents_must_converge and self._are_relevant_parents_finished(n):
                    if self._all_parents_met_convergence_criteria(n):
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
            if obj.do_not_run is False and not obj.job and obj.unified_job_template:
                return False
            elif obj.job and obj.job.status not in ['successful', 'failed', 'canceled', 'error']:
                return False
        return True

    def has_workflow_failed(self):
        failed_nodes = []
        res = False
        failed_path_nodes_id_status = []
        failed_unified_job_template_node_ids = []

        for node in self.nodes:
            obj = node['node_object']
            if obj.do_not_run is False and obj.unified_job_template is None:
                failed_nodes.append(node)
            elif obj.job and obj.job.status in ['failed', 'canceled', 'error']:
                failed_nodes.append(node)

        for node in failed_nodes:
            obj = node['node_object']
            if (len(self.get_children(obj, 'failure_nodes')) +
                    len(self.get_children(obj, 'always_nodes'))) == 0:
                if obj.unified_job_template is None:
                    res = True
                    failed_unified_job_template_node_ids.append(str(obj.id))
                else:
                    res = True
                    failed_path_nodes_id_status.append((str(obj.id), obj.job.status))

        if res is True:
            s = _("No error handling path for workflow job node(s) [{node_status}]. Workflow job "
                  "node(s) missing unified job template and error handling path [{no_ufjt}].")
            parms = {
                'node_status': '',
                'no_ufjt': '',
            }
            if len(failed_path_nodes_id_status) > 0:
                parms['node_status'] = ",".join(["({},{})".format(id, status) for id, status in failed_path_nodes_id_status])
            if len(failed_unified_job_template_node_ids) > 0:
                parms['no_ufjt'] = ",".join(failed_unified_job_template_node_ids)
            return True, smart_text(s.format(**parms))
        return False, None

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
            if n.do_not_run is False and not n.job and n.unified_job_template:
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
            if p.do_not_run is True:
                pass
            elif p.job:
                if p.job.status == 'successful':
                    if node in (self.get_children(p, 'success_nodes') +
                                self.get_children(p, 'always_nodes')):
                        return False
                elif p.job.status in ['failed', 'error', 'canceled']:
                    if node in (self.get_children(p, 'failure_nodes') +
                                self.get_children(p, 'always_nodes')):
                        return False
                else:
                    return False
            elif not p.do_not_run and p.unified_job_template is None:
                if node in (self.get_children(p, 'failure_nodes') +
                            self.get_children(p, 'always_nodes')):
                    return False
            else:
                return False
        return True


    r'''
    determine if the current node is a convergence node by checking if all the
    parents are finished then checking to see if all parents meet the needed
    path criteria to run the convergence child.
    (i.e. parent must fail, parent must succeed, etc. to proceed)

    Return a list object
    '''
    def mark_dnr_nodes(self):
        root_nodes = self.get_root_nodes()
        nodes_marked_do_not_run = []

        for node in self.sort_nodes_topological():
            obj = node['node_object']
            parent_nodes = [p['node_object'] for p in self.get_parents(obj)]
            if not obj.do_not_run and not obj.job and node not in root_nodes:
                if obj.all_parents_must_converge:
                    if any(p.do_not_run for p in parent_nodes) or not self._all_parents_met_convergence_criteria(node):
                        obj.do_not_run = True
                        nodes_marked_do_not_run.append(node)
                else:
                    if self._are_all_nodes_dnr_decided(parent_nodes):
                        if self._should_mark_node_dnr(node, parent_nodes):
                            obj.do_not_run = True
                            nodes_marked_do_not_run.append(node)

        return [n['node_object'] for n in nodes_marked_do_not_run]
