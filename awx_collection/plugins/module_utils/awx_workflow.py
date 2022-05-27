#!/usr/bin/python
import copy

from .awx_organization import get_resource_access_list
from .awx_schedule import get_schedules
from .export_tools import parse_extra_vars_to_json
from .awx_notification import get_notifications_by_unified_job_template
from .awx_request import get_awx_resources
import requests

def filter_end_nodes(workflow_nodes, sorted_nodes, begin_sorting):
    for workflow_index, workflow_node in enumerate(workflow_nodes):
        if len(workflow_node['success_nodes']) == 0 and len(workflow_node['failure_nodes']) == 0 and len(workflow_node['always_nodes']) == 0:
            if begin_sorting:
                workflow_node['extra_data'] = parse_extra_vars_to_json(workflow_node['extra_data'])
                workflow_node['identifier'] = str(workflow_node['id'])
                sorted_nodes.append(copy.deepcopy(workflow_node))
            workflow_nodes.pop(workflow_index)
    return sorted_nodes, workflow_nodes

def search_for_pior_nodes(current_node, remain_nodes, prior_nodes):
    for workflow_index, workflow_node in enumerate(remain_nodes):
        if current_node['id'] in workflow_node['success_nodes']:
            workflow_node['extra_data'] = parse_extra_vars_to_json(workflow_node['extra_data'])
            workflow_node['identifier'] = str(workflow_node['id'])
            prior_nodes.append(copy.deepcopy(workflow_node))
            remain_nodes[workflow_index]['success_nodes'].remove(current_node['id'])
        if current_node['id'] in workflow_node['failure_nodes']:
            workflow_node['extra_data'] = parse_extra_vars_to_json(workflow_node['extra_data'])
            workflow_node['identifier'] = str(workflow_node['id'])
            prior_nodes.append(copy.deepcopy(workflow_node))
            remain_nodes[workflow_index]['failure_nodes'].remove(current_node['id'])
        if current_node['id'] in workflow_node['always_nodes']:
            workflow_node['extra_data'] = parse_extra_vars_to_json(workflow_node['extra_data'])
            workflow_node['identifier'] = str(workflow_node['id'])
            prior_nodes.append(copy.deepcopy(workflow_node))
            remain_nodes[workflow_index]['always_nodes'].remove(current_node['id'])
    return prior_nodes, remain_nodes

def sort_workflow_job_template_nodes(workflow_nodes, sorted_nodes, begin_sorting):
    sorted_nodes, remain_nodes = filter_end_nodes(workflow_nodes, sorted_nodes, begin_sorting)
    for current_node in sorted_nodes:
        sorted_nodes, remain_nodes= search_for_pior_nodes(current_node, remain_nodes, sorted_nodes)
    if len(remain_nodes) > 0:
        return sort_workflow_job_template_nodes(workflow_nodes=remain_nodes, sorted_nodes=sorted_nodes, begin_sorting=False)
    return sorted_nodes

def remove_duplicate_workflow_job_template_nodes(sorted_nodes):
    seen = set()
    filtered_nodes = []
    for node in sorted_nodes:
        if node['identifier'] not in seen:
            seen.add(node['identifier'])
            filtered_nodes.append(node)
        else:
            # ignore current duplicate node and move original node to the end of the array
            existing_node_index = next((index for (index, search_node) in enumerate(filtered_nodes) if search_node['identifier'] == node['identifier']), None)
            original_node = filtered_nodes.pop(existing_node_index)
            filtered_nodes.append(original_node)
    return filtered_nodes

def get_workflow_job_templates(organization, notification_templates, existing_members_set, awx_auth):
    workflows = []
    unified_job_template_type = 'workflow_job_templates'
    workflow_job_templates = get_awx_resources(uri='/api/v2/workflow_job_templates/?organization=' + str(organization['id']), previousPageResults=[], awx_auth=awx_auth)
    for workflow_job_template in workflow_job_templates:
        workflow_job_template['nodes'] = get_awx_resources(uri='/api/v2/workflow_job_template_nodes/?workflow_job_template=' + str(workflow_job_template['id']), previousPageResults=[], awx_auth=awx_auth)
        notification_templates, workflow_job_template['notification_templates_success'] = get_notifications_by_unified_job_template(unified_job_template_type, workflow_job_template['id'], 'notification_templates_success', notification_templates, awx_auth)
        notification_templates, workflow_job_template['notification_templates_started'] = get_notifications_by_unified_job_template(unified_job_template_type, workflow_job_template['id'], 'notification_templates_started', notification_templates, awx_auth)
        notification_templates, workflow_job_template['notification_templates_error'] = get_notifications_by_unified_job_template(unified_job_template_type, workflow_job_template['id'], 'notification_templates_error', notification_templates, awx_auth)
        workflow_job_template['extra_vars'] = parse_extra_vars_to_json(workflow_job_template['extra_vars'])
        workflow_job_template['survey_spec'] = requests.get(url='https://'+awx_auth['host']+'/api/v2/workflow_job_templates/' + str(workflow_job_template['id']) + '/survey_spec/', auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['validate_certs']).json()
        workflow_job_template['schedules'] = get_schedules(workflow_job_template, awx_auth)
        workflow_job_template['sorted_nodes'] = sort_workflow_job_template_nodes(workflow_nodes=workflow_job_template['workflow_nodes'], sorted_nodes=[], begin_sorting=True)
        workflow_job_template['sorted_nodes'] = remove_duplicate_workflow_job_template_nodes(workflow_job_template['sorted_nodes'])
        workflow_job_template.pop('workflow_nodes', None)
        workflow_job_template['roles'], existing_members_set = get_resource_access_list('workflow_job_templates', workflow_job_template['id'], existing_members_set, awx_auth)
        
        workflows.append(workflow_job_template)
    return workflows, notification_templates

