#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: workflow_job_template_node
author: "John Westcott IV (@john-westcott-iv)"
short_description: create, update, or destroy Automation Platform Controller workflow job template nodes.
description:
    - Create, update, or destroy Automation Platform Controller workflow job template nodes.
    - Use this to build a graph for a workflow, which dictates what the workflow runs.
    - You can create nodes first, and link them afterwards, and not worry about ordering.
      For failsafe referencing of a node, specify identifier, WFJT, and organization.
      With those specified, you can choose to modify or not modify any other parameter.
options:
    extra_data:
      description:
        - Variables to apply at launch time.
        - Will only be accepted if job template prompts for vars or has a survey asking for those vars.
      type: dict
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
        - Omit if creating an approval node.
        - This parameter is mutually exclusive with C(approval_node).
      type: str
    lookup_organization:
      description:
        - Organization the inventories, job template, project, inventory source the unified_job_template exists in.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
    approval_node:
      description:
        - A dictionary of Name, description, and timeout values for the approval node.
        - This parameter is mutually exclusive with C(unified_job_template).
      type: dict
      suboptions:
        name:
          description:
            - Name of this workflow approval template.
          type: str
          required: True
        description:
          description:
            - Optional description of this workflow approval template.
          type: str
        timeout:
          description:
            - The amount of time (in seconds) before the approval node expires and fails.
          type: int
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
    execution_environment:
      description:
        - Execution Environment applied as a prompt, assuming jot template prompts for execution environment
      type: str
    forks:
      description:
        - Forks applied as a prompt, assuming job template prompts for forks
      type: int
    instance_groups:
      description:
        - List of Instance Groups applied as a prompt, assuming job template prompts for instance groups
      type: list
      elements: str
    job_slice_count:
      description:
        - Job Slice Count applied as a prompt, assuming job template prompts for job slice count
      type: int
    labels:
      description:
        - List of labels applied as a prompt, assuming job template prompts for labels
      type: list
      elements: str
    timeout:
      description:
        - Timeout applied as a prompt, assuming job template prompts for timeout
      type: int
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Create a node, follows workflow_job_template example
  workflow_job_template_node:
    identifier: my-first-node
    workflow: example-workflow
    unified_job_template: jt-for-node-use
    organization: Default  # organization of workflow job template
    extra_data:
      foo_key: bar_value

- name: Create parent node for prior node
  workflow_job_template_node:
    identifier: my-root-node
    workflow: example-workflow
    unified_job_template: jt-for-node-use
    organization: Default
    success_nodes:
      - my-first-node

- name: Create workflow with 2 Job Templates and an approval node in between
  block:
  - name: Create a workflow job template
    tower_workflow_job_template:
      name: my-workflow-job-template
      ask_scm_branch_on_launch: true
      organization: Default

  - name: Create 1st node
    tower_workflow_job_template_node:
      identifier: my-first-node
      workflow_job_template: my-workflow-job-template
      unified_job_template: some_job_template
      organization: Default

  - name: Create 2nd approval node
    tower_workflow_job_template_node:
      identifier: my-second-approval-node
      workflow_job_template: my-workflow-job-template
      organization: Default
      approval_node:
        description: "Do this?"
        name: my-second-approval-node
        timeout: 3600

  - name: Create 3rd node
    tower_workflow_job_template_node:
      identifier: my-third-node
      workflow_job_template: my-workflow-job-template
      unified_job_template: some_other_job_template
      organization: Default

  - name: Link 1st node to 2nd Approval node
    tower_workflow_job_template_node:
      identifier: my-first-node
      workflow_job_template: my-workflow-job-template
      organization: Default
      success_nodes:
        - my-second-approval-node

  - name: Link 2nd Approval Node 3rd node
    tower_workflow_job_template_node:
      identifier: my-second-approval-node
      workflow_job_template: my-workflow-job-template
      organization: Default
      success_nodes:
        - my-third-node
'''

from ..module_utils.controller_api import ControllerAPIModule


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
        lookup_organization=dict(),
        approval_node=dict(type='dict'),
        all_parents_must_converge=dict(type='bool'),
        success_nodes=dict(type='list', elements='str'),
        always_nodes=dict(type='list', elements='str'),
        failure_nodes=dict(type='list', elements='str'),
        credentials=dict(type='list', elements='str'),
        execution_environment=dict(type='str'),
        forks=dict(type='int'),
        instance_groups=dict(type='list', elements='str'),
        job_slice_count=dict(type='int'),
        labels=dict(type='list', elements='str'),
        timeout=dict(type='int'),
        state=dict(choices=['present', 'absent'], default='present'),
    )
    mutually_exclusive = [("unified_job_template", "approval_node")]
    required_if = [
        ['state', 'absent', ['identifier']],
        ['state', 'present', ['identifier']],
        ['state', 'present', ['unified_job_template', 'approval_node', 'success_nodes', 'always_nodes', 'failure_nodes'], True],
    ]

    # Create a module for ourselves
    module = ControllerAPIModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
    )

    # Extract our parameters
    identifier = module.params.get('identifier')
    state = module.params.get('state')
    approval_node = module.params.get('approval_node')
    new_fields = {}
    lookup_organization = module.params.get('lookup_organization')
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
        wfjt_data = module.get_one('workflow_job_templates', name_or_id=workflow_job_template, **{'data': wfjt_search_fields})
        if wfjt_data is None:
            module.fail_json(
                msg="The workflow {0} in organization {1} was not found on the controller instance server".format(workflow_job_template, organization)
            )
        workflow_job_template_id = wfjt_data['id']
        search_fields['workflow_job_template'] = new_fields['workflow_job_template'] = workflow_job_template_id

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('workflow_job_template_nodes', **{'data': search_fields})

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)

    # Set lookup data to use
    search_fields = {}
    if lookup_organization:
        search_fields['organization'] = module.resolve_name_to_id('organizations', lookup_organization)

    unified_job_template = module.params.get('unified_job_template')
    if unified_job_template:
        new_fields['unified_job_template'] = module.get_one('unified_job_templates', name_or_id=unified_job_template, **{'data': search_fields})['id']
    inventory = module.params.get('inventory')
    if inventory:
        new_fields['inventory'] = module.resolve_name_to_id('inventories', inventory)

    # Create the data that gets sent for create and update
    for field_name in (
        'identifier',
        'extra_data',
        'scm_branch',
        'job_type',
        'job_tags',
        'skip_tags',
        'limit',
        'diff_mode',
        'verbosity',
        'all_parents_must_converge',
        'forks',
        'job_slice_count',
        'timeout',
    ):
        field_val = module.params.get(field_name)
        if field_val:
            new_fields[field_name] = field_val

    association_fields = {}
    for association in ('always_nodes', 'success_nodes', 'failure_nodes', 'credentials', 'instance_groups', 'labels'):
        name_list = module.params.get(association)
        if name_list is None:
            continue
        id_list = []
        for sub_name in name_list:
            if association in ['credentials', 'instance_groups', 'labels']:
                sub_obj = module.get_one(association, name_or_id=sub_name)
            else:
                endpoint = 'workflow_job_template_nodes'
                lookup_data = {'identifier': sub_name}
                if workflow_job_template_id:
                    lookup_data['workflow_job_template'] = workflow_job_template_id
                sub_obj = module.get_one(endpoint, **{'data': lookup_data})
            if sub_obj is None:
                module.fail_json(msg='Could not find {0} entry with name {1}'.format(association, sub_name))
            id_list.append(sub_obj['id'])
        association_fields[association] = id_list

    execution_environment = module.params.get('execution_environment')
    if execution_environment is not None:
        if execution_environment == '':
            new_fields['execution_environment'] = ''
        else:
            ee = module.get_one('execution_environments', name_or_id=execution_environment)
            if ee is None:
                module.fail_json(msg='could not find execution_environment entry with name {0}'.format(execution_environment))
            else:
                new_fields['execution_environment'] = ee['id']

    # In the case of a new object, the utils need to know it is a node
    new_fields['type'] = 'workflow_job_template_node'

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item,
        new_fields,
        endpoint='workflow_job_template_nodes',
        item_type='workflow_job_template_node',
        auto_exit=not approval_node,
        associations=association_fields,
    )

    # Create approval node unified template or update existing
    if approval_node:
        # Set Approval Fields
        new_fields = {}

        # Extract Parameters
        if approval_node.get('name') is None:
            module.fail_json(msg="Approval node name is required to create approval node.")
        if approval_node.get('name') is not None:
            new_fields['name'] = approval_node['name']
        if approval_node.get('description') is not None:
            new_fields['description'] = approval_node['description']
        if approval_node.get('timeout') is not None:
            new_fields['timeout'] = approval_node['timeout']

        # Find created workflow node ID
        search_fields = {'identifier': identifier}
        search_fields['workflow_job_template'] = workflow_job_template_id
        workflow_job_template_node = module.get_one('workflow_job_template_nodes', **{'data': search_fields})
        workflow_job_template_node_id = workflow_job_template_node['id']
        module.json_output['workflow_node_id'] = workflow_job_template_node_id
        existing_item = None
        # Due to not able to lookup workflow_approval_templates, find the existing item in another place
        if workflow_job_template_node['related'].get('unified_job_template') is not None:
            existing_item = module.get_endpoint(workflow_job_template_node['related']['unified_job_template'])['json']
        approval_endpoint = 'workflow_job_template_nodes/{0}/create_approval_template/'.format(workflow_job_template_node_id)
        module.create_or_update_if_needed(
            existing_item, new_fields, endpoint=approval_endpoint, item_type='workflow_job_template_approval_node', associations=association_fields
        )
    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
