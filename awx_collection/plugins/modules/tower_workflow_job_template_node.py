#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_workflow_job_template_node
author: "John Westcott IV (@john-westcott-iv)"
short_description: create, update, or destroy Ansible Tower workflow job template nodes.
description:
    - Create, update, or destroy Ansible Tower workflow job template nodes.
    - Use this to build a graph for a workflow, which dictates what the workflow runs.
    - Replaces the deprecated tower_workflow_template module schema command.
    - You can create nodes first, and link them afterwards, and not worry about ordering.
      For failsafe referencing of a node, specify identifier, WFJT, and organization.
      With those specified, you can choose to modify or not modify any other parameter.
options:
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

from ..module_utils.tower_api import TowerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        identifier=dict(required=True),
        workflow_job_template=dict(required=True, aliases=['workflow']),
        organization=dict(),
        extra_data=dict(type='dict'),
        inventory=dict(),
        scm_branch=dict(),
        job_type=dict(choices=['run', 'check']),
        job_tags=dict(),
        skip_tags=dict(),
        limit=dict(),
        diff_mode=dict(type='bool'),
        verbosity=dict(choices=['0', '1', '2', '3', '4', '5']),
        unified_job_template=dict(),
        all_parents_must_converge=dict(type='bool'),
        success_nodes=dict(type='list', elements='str'),
        always_nodes=dict(type='list', elements='str'),
        failure_nodes=dict(type='list', elements='str'),
        credentials=dict(type='list', elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    identifier = module.params.get('identifier')
    state = module.params.get('state')

    new_fields = {}
    search_fields = {'identifier': identifier}

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    workflow_job_template = module.params.get('workflow_job_template')
    workflow_job_template_id = None
    if workflow_job_template:
        wfjt_search_fields = {}
        organization = module.params.get('organization')
        if organization:
            organization_id = module.resolve_name_to_id('organizations', organization)
            wfjt_search_fields['organization'] = organization_id
        wfjt_data = module.get_one('workflow_job_templates', name_or_id=workflow_job_template, **{
            'data': wfjt_search_fields
        })
        if wfjt_data is None:
            module.fail_json(msg="The workflow {0} in organization {1} was not found on the Tower server".format(
                workflow_job_template, organization
            ))
        workflow_job_template_id = wfjt_data['id']
        search_fields['workflow_job_template'] = new_fields['workflow_job_template'] = workflow_job_template_id

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('workflow_job_template_nodes', **{'data': search_fields})

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)

    unified_job_template = module.params.get('unified_job_template')
    if unified_job_template:
        new_fields['unified_job_template'] = module.resolve_name_to_id('unified_job_templates', unified_job_template)

    inventory = module.params.get('inventory')
    if inventory:
        new_fields['inventory'] = module.resolve_name_to_id('inventories', inventory)

    # Create the data that gets sent for create and update
    for field_name in (
            'identifier', 'extra_data', 'scm_branch', 'job_type', 'job_tags', 'skip_tags',
            'limit', 'diff_mode', 'verbosity', 'all_parents_must_converge',):
        field_val = module.params.get(field_name)
        if field_val:
            new_fields[field_name] = field_val

    association_fields = {}
    for association in ('always_nodes', 'success_nodes', 'failure_nodes', 'credentials'):
        name_list = module.params.get(association)
        if name_list is None:
            continue
        id_list = []
        for sub_name in name_list:
            if association == 'credentials':
                endpoint = 'credentials'
                lookup_data = {'name': sub_name}
            else:
                endpoint = 'workflow_job_template_nodes'
                lookup_data = {'identifier': sub_name}
                if workflow_job_template_id:
                    lookup_data['workflow_job_template'] = workflow_job_template_id
            sub_obj = module.get_one(endpoint, **{'data': lookup_data})
            if sub_obj is None:
                module.fail_json(msg='Could not find {0} entry with name {1}'.format(association, sub_name))
            id_list.append(sub_obj['id'])
        if id_list:
            association_fields[association] = id_list

    # In the case of a new object, the utils need to know it is a node
    new_fields['type'] = 'workflow_job_template_node'

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item, new_fields,
        endpoint='workflow_job_template_nodes', item_type='workflow_job_template_node',
        associations=association_fields
    )


if __name__ == '__main__':
    main()
