#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>, Sean Sullivan <ssulliva@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_workflow_job_template_node
author: "John Westcott IV (@john-westcott-iv), Sean Sullivan (@Wilk42)"
version_added: "2.9"
short_description: create, update, or destroy Ansible Tower workflow job template graphs.
description:
    - Create, update, or destroy Ansible Tower workflow job template graphs.
    - Use this to build a graph for a workflow, which dictates what the workflow runs.
    - Replaces the deprecated tower_workflow_template module schema command.
    - This module takes a josn list of inputs to first create nodes, then link them, and does not worry about ordering.
      For failsafe referencing of a node, specify identifier, WFJT, and organization.
      With those specified, you can choose to modify or not modify any other parameter.
options:
    workflow_job_template:
      description:
        - The workflow job template the node exists in.
        - Used for looking up the node, cannot be modified after creation.
      required: True
      type: str
      aliases:
        - workflow
    organization:
      description:
        - The organization of the workflow job template the node exists in.
        - Used for looking up the workflow, not a direct model field.
      type: str
    schema:
      description:
        - A json list of nodes and their coresponding options.
      type: str
    destroy_current_schema:
      description:
        - Set in order to destroy current schema on the workflow.
        - This option is used for full schema update, if not used, nodes not described in schema will persist and keep current associations and links.
      type: Bool
      default: False
schema_options:
    extra_data:
      description:
        - Variables to apply at launch time.
        - Will only be accepted if job template prompts for vars or has a survey asking for those vars.
      type: dict
      default: {}
    inventory:
      description:
        - Inventory applied as a prompt, if job template prompts for inventory
      type: str
    scm_branch:
      description:
        - SCM branch applied as a prompt, if job template prompts for SCM branch
      type: str
    job_type:
      description:
        - Job type applied as a prompt, if job template prompts for job type
      type: str
      choices:
        - 'run'
        - 'check'
    job_tags:
      description:
        - Job tags applied as a prompt, if job template prompts for job tags
      type: str
    skip_tags:
      description:
        - Tags to skip, applied as a prompt, if job tempalte prompts for job tags
      type: str
    limit:
      description:
        - Limit to act on, applied as a prompt, if job template prompts for limit
      type: str
    diff_mode:
      description:
        - Run diff mode, applied as a prompt, if job template prompts for diff mode
      type: bool
    verbosity:
      description:
        - Verbosity applied as a prompt, if job template prompts for verbosity
      type: str
      choices:
        - '0'
        - '1'
        - '2'
        - '3'
        - '4'
        - '5'
    unified_job_template:
      description:
        - Name of unified job template to run in the workflow.
        - Can be a job template, project, inventory source, etc.
        - Omit if creating an approval node (not yet implemented).
      type: str
    all_parents_must_converge:
      description:
        - If enabled then the node will only run if all of the parent nodes have met the criteria to reach this node
      type: bool
    identifier:
      description:
        - An identifier for this node that is unique within its workflow.
        - It is copied to workflow job nodes corresponding to this node.
      required: True
      type: str
    always_nodes:
      description:
        - Nodes that will run after this node completes.
        - List of node identifiers.
      type: list
      elements: str
    success_nodes:
      description:
        - Nodes that will run after this node on success.
        - List of node identifiers.
      type: list
      elements: str
    failure_nodes:
      description:
        - Nodes that will run after this node on failure.
        - List of node identifiers.
      type: list
      elements: str
    credentials:
      description:
        - Credentials to be applied to job as launch-time prompts.
        - List of credential names.
        - Uniqueness is not handled rigorously.
      type: list
      elements: str
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str

extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Create a node, follows tower_workflow_job_template example
  tower_workflow_job_template_node:
    identifier: my-first-node
    workflow: example-workflow
    unified_job_template: jt-for-node-use
    organization: Default  # organization of workflow job template
    extra_data:
      foo_key: bar_value

- name: Create parent node for prior node
  tower_workflow_job_template_node:
    identifier: my-root-node
    workflow: example-workflow
    unified_job_template: jt-for-node-use
    organization: Default
    success_nodes:
      - my-first-node
'''

from ..module_utils.tower_api import TowerModule
from ansible.errors import AnsibleError

response = []


def create_schema_nodes(module, schema, workflow_id):
    
    for workflow_node in schema:
        workflow_node_fields = {}
        search_fields = {}
        association_fields = {}
        
        # Set Search fields
        search_fields['workflow_job_template'] = workflow_node_fields['workflow_job_template'] = workflow_id

        # Lookup Job Template ID
        try:
            if workflow_node['unified_job_template']['name']:
              search_fields = {'name': workflow_node['unified_job_template']['name']}
              if workflow_node['unified_job_template']['organization']['name']:
                  organization_id = module.resolve_name_to_id('organizations', workflow_node['unified_job_template']['organization']['name'])
                  search_fields['organization'] = organization_id
              job_template = module.get_one('job_templates', **{'data': search_fields})
              workflow_node_fields['unified_job_template'] = job_template['id']
        except:
            pass

        # Lookup Inventory ID
        try:
            if workflow_node['inventory']:
                workflow_node_fields['inventory'] = module.resolve_name_to_id('inventories', workflow_node['inventory'])
        except:
            pass

        # Lookup Values for other fields

        for field_name in (
                'identifier', 'extra_data', 'scm_branch', 'job_type', 'job_tags', 'skip_tags',
                'limit', 'diff_mode', 'verbosity', 'all_parents_must_converge', 'state',):
            try:
                if workflow_node[field_name]:
                    workflow_node_fields[field_name] = workflow_node[field_name]
                if workflow_node['identifier']:
                    search_fields = {'identifier': workflow_node['identifier']}
            except:
                pass

        # Attempt to look up an existing item based on the provided data
        existing_item = module.get_one('workflow_job_template_nodes', **{'data': search_fields})

        # Determine if state is present or absent.
        state = True
        if 'state' in workflow_node:
            if workflow_node['state'] == 'absent':
                state = False

        if state:
            response.append(
              module.create_or_update_if_needed(
                  existing_item, workflow_node_fields,
                  endpoint='workflow_job_template_nodes', item_type='workflow_job_template_node', on_continue=True,
              )
            )
        else:
            # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
            response.append(
              module.delete_if_needed(
                  existing_item, on_continue=True,
              )
            )


def create_schema_nodes_association(module, schema, workflow_id):

    for workflow_node in schema:
        workflow_node_fields = {}
        search_fields = {}
        association_fields = {}

        # Set Search fields
        search_fields['workflow_job_template'] = workflow_node_fields['workflow_job_template'] = workflow_id

        # Lookup Values for other fields
        try:
            if workflow_node['identifier']:
                workflow_node_fields['identifier'] = workflow_node['identifier']
                search_fields = {'identifier': workflow_node['identifier']}
        except:
            pass

        # Attempt to look up an existing item based on the provided data
        existing_item = module.get_one('workflow_job_template_nodes', **{'data': search_fields})

        if 'state' in workflow_node:
            if workflow_node['state'] == 'absent':
                continue

        # Get id's for association fields
        association_fields = {}
        #raise AnsibleError('var error:  {}'.format(len(workflow_node['related']['success_nodes'])))
        for association in ('always_nodes', 'success_nodes', 'failure_nodes', 'credentials'):
            # Extract out information if it exists
            try:
                # Test if it is defined, else move to next association.
                if not workflow_node['related'][association]:
                    continue
                else:
                    id_list = []
                    for sub_name in workflow_node['related'][association]:
                        if association == 'credentials':
                            endpoint = 'credentials'
                            lookup_data = {'name': sub_name['name']}
                        else:
                            endpoint = 'workflow_job_template_nodes'
                            lookup_data = {'identifier': sub_name['identifier']}
                            lookup_data['workflow_job_template'] = workflow_id
                        sub_obj = module.get_one(endpoint, **{'data': lookup_data})
                        if sub_obj is None:
                            module.fail_json(msg='Could not find {0} entry with name {1}'.format(association, sub_name))
                        id_list.append(sub_obj['id'])
                        temp = sub_obj['id']
                    if id_list:
                        association_fields[association] = id_list
                
                response.append(
                  module.create_or_update_if_needed(
                      existing_item, workflow_node_fields,
                      endpoint='workflow_job_template_nodes', item_type='workflow_job_template_node', on_continue=True,
                      associations=association_fields,
                  )
                )
            except:
                raise AnsibleError('var error:  {}'.format(association))
                continue


def destroy_schema_nodes(module, workflow_id):
        search_fields = {}

        # Search for existing nodes.
        search_fields['workflow_job_template'] = workflow_id
        existing_items = module.get_all_endpoint('workflow_job_template_nodes', **{'data': search_fields})

        # Loop through found fields
        for workflow_node in existing_items['json']['results']:
            search_fields = {}
            # Set fields
            search_fields['workflow_job_template'] = workflow_id
            search_fields['identifier'] = workflow_node['identifier']
            # Search for existing item
            existing_item = module.get_one('workflow_job_template_nodes', **{'data': search_fields})
            response.append(
              module.delete_if_needed(
                  existing_item, on_continue=True,
              )
            )


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        workflow_job_template=dict(required=True, aliases=['workflow']),
        organization=dict(),
        schema=dict(required=True, type='list', elements='dict'),
        destroy_current_schema=dict(type='bool', default=False),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    schema = None
    if module.params.get('schema'):
        schema = module.params.get('schema')
    destroy_current_schema = module.params.get('destroy_current_schema')

    new_fields = {}

    node_loop = ''

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    workflow_job_template = module.params.get('workflow_job_template')
    workflow_job_template_id = None
    if workflow_job_template:
        wfjt_search_fields = {'name': workflow_job_template}
        organization = module.params.get('organization')
        if organization:
            organization_id = module.resolve_name_to_id('organizations', organization)
            wfjt_search_fields['organization'] = organization_id
        wfjt_data = module.get_one('workflow_job_templates', **{'data': wfjt_search_fields})
        if wfjt_data is None:
            module.fail_json(msg="The workflow {0} in organization {1} was not found on the Tower server".format(
                workflow_job_template, organization
            ))
        workflow_job_template_id = wfjt_data['id']

    # Work thorugh and lookup value for schema fields
    # Destroy current nodes if selected.
    if destroy_current_schema:
        destroy_schema_nodes(module, workflow_job_template_id)
    # Create Schema Nodes
    create_schema_nodes(module, schema, workflow_job_template_id)
    # Create Schema Associations
    create_schema_nodes_association(module, schema, workflow_job_template_id)
    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
