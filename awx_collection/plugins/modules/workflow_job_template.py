#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: workflow_job_template
author: "John Westcott IV (@john-westcott-iv)"
short_description: create, update, or destroy Automation Platform Controller workflow job templates.
description:
    - Create, update, or destroy Automation Platform Controller workflow job templates.
    - Replaces the deprecated tower_workflow_template module.
    - Use workflow_job_template_node after this, or use the schema parameter to build the workflow's graph
options:
    name:
      description:
        - Name of this workflow job template.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name.
      type: str
    copy_from:
      description:
        - Name or id to copy the workflow job template from.
        - This will copy an existing workflow job template and change any parameters supplied.
        - The new workflow job template name will be the one provided in the name parameter.
        - The organization parameter is not used in this, to facilitate copy from one organization to another.
        - Provide the id or use the lookup plugin to provide the id if multiple workflow job templates share the same name.
      type: str
    description:
      description:
        - Optional description of this workflow job template.
      type: str
    extra_vars:
      description:
        - Variables which will be made available to jobs ran inside the workflow.
      type: dict
    organization:
      description:
        - Organization the workflow job template exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
    allow_simultaneous:
      description:
        - Allow simultaneous runs of the workflow job template.
      type: bool
    ask_variables_on_launch:
      description:
        - Prompt user for C(extra_vars) on launch.
      type: bool
    inventory:
      description:
        - Inventory applied as a prompt, assuming job template prompts for inventory
      type: str
    limit:
      description:
        - Limit applied as a prompt, assuming job template prompts for limit
      type: str
    scm_branch:
      description:
        - SCM branch applied as a prompt, assuming job template prompts for SCM branch
      type: str
    ask_inventory_on_launch:
      description:
        - Prompt user for inventory on launch of this workflow job template
      type: bool
    ask_scm_branch_on_launch:
      description:
        - Prompt user for SCM branch on launch of this workflow job template
      type: bool
    ask_limit_on_launch:
      description:
        - Prompt user for limit on launch of this workflow job template
      type: bool
    webhook_service:
      description:
        - Service that webhook requests will be accepted from
      type: str
      choices:
        - github
        - gitlab
    webhook_credential:
      description:
        - Personal Access Token for posting back the status to the service API
      type: str
    survey_enabled:
      description:
        - Setting that variable will prompt the user for job type on the
          workflow launch.
      type: bool
    survey_spec:
      description:
        - The definition of the survey associated to the workflow.
      type: dict
      aliases:
        - survey
    labels:
      description:
        - The labels applied to this job template
      type: list
      elements: str
    state:
      description:
        - Desired state of the resource.
      choices:
        - present
        - absent
      default: "present"
      type: str
    notification_templates_started:
      description:
        - list of notifications to send on start
      type: list
      elements: str
    notification_templates_success:
      description:
        - list of notifications to send on success
      type: list
      elements: str
    notification_templates_error:
      description:
        - list of notifications to send on error
      type: list
      elements: str
    notification_templates_approvals:
      description:
        - list of notifications to send on start
      type: list
      elements: str
    schema:
      description:
        - A json list of nodes and their coresponding options. The following suboptions describe a single node.
      type: list
      elements: dict
      suboptions:
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
        state:
          description:
            - Desired state of the resource.
          choices: ["present", "absent"]
          default: "present"
          type: str
        unified_job_template:
          description:
            - Name of unified job template to run in the workflow.
            - Can be a job template, project sync, inventory source sync, etc.
            - Omit if creating an approval node (not yet implemented).
          type: dict
          suboptions:
            organization:
              description:
                - Name of key for use in model for organizational reference
                - Only Valid and used if referencing a job template or project sync
                - This parameter is mutually exclusive with suboption C(inventory).
              type: dict
              suboptions:
                name:
                  description:
                    - The organization of the job template or project sync the node exists in.
                    - Used for looking up the job template or project sync, not a direct model field.
                  type: str
            inventory:
              description:
                - Name of key for use in model for organizational reference
                - Only Valid and used if referencing an inventory sync
                - This parameter is mutually exclusive with suboption C(organization).
              type: dict
              suboptions:
                organization:
                  description:
                    - Name of key for use in model for organizational reference
                  type: dict
                  suboptions:
                    name:
                      description:
                        - The organization of the inventory the node exists in.
                        - Used for looking up the job template or project, not a direct model field.
                      type: str
            name:
              description:
                - Name of unified job template to run in the workflow.
                - Can be a job template, project, inventory source, etc.
              type: str
            description:
              description:
                - Optional description of this workflow approval template.
              type: str
            type:
              description:
                - Name of unified job template type to run in the workflow.
                - Can be a job_template, project, inventory_source, workflow_approval.
              type: str
            timeout:
              description:
                - The amount of time (in seconds) to wait before Approval is canceled. A value of 0 means no timeout.
                - Only Valid and used if referencing an Approval Node
              default: 0
              type: int
        related:
          description:
            - Related items to this workflow node.
            - Must include credentials, failure_nodes, always_nodes, success_nodes, even if empty.
          type: dict
          suboptions:
            always_nodes:
              description:
                - Nodes that will run after this node completes.
                - List of node identifiers.
              type: list
              suboptions:
                identifier:
                  description:
                    - Identifier of Node that will run after this node completes given this option.
                  elements: str
            success_nodes:
              description:
                - Nodes that will run after this node on success.
                - List of node identifiers.
              type: list
              suboptions:
                identifier:
                  description:
                    - Identifier of Node that will run after this node completes given this option.
                  elements: str
            failure_nodes:
              description:
                - Nodes that will run after this node on failure.
                - List of node identifiers.
              type: list
              suboptions:
                identifier:
                  description:
                    - Identifier of Node that will run after this node completes given this option.
                  elements: str
            credentials:
              description:
                - Credentials to be applied to job as launch-time prompts.
                - List of credential names.
                - Uniqueness is not handled rigorously.
              type: list
              suboptions:
                name:
                  description:
                    - Name Credentials to be applied to job as launch-time prompts.
                  elements: str
    destroy_current_schema:
      description:
        - Set in order to destroy current schema on the workflow.
        - This option is used for full schema update, if not used, nodes not described in schema will persist and keep current associations and links.
      type: bool
      default: False

extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Create a workflow job template
  workflow_job_template:
    name: example-workflow
    description: created by Ansible Playbook
    organization: Default

- name: Create a workflow job template with schema in template
  awx.awx.workflow_job_template:
    name: example-workflow
    inventory: Demo Inventory
    extra_vars: {'foo': 'bar', 'another-foo': {'barz': 'bar2'}}
    schema:
      - identifier: node101
        unified_job_template:
          name: example-project
          inventory:
            organization:
              name: Default
          type: inventory_source
        related:
          success_nodes: []
          failure_nodes:
            - identifier: node201
          always_nodes: []
          credentials: []
      - identifier: node201
        unified_job_template:
          organization:
            name: Default
          name: job template 1
          type: job_template
        credentials: []
        related:
          success_nodes:
            - identifier: node301
          failure_nodes: []
          always_nodes: []
          credentials: []
      - identifier: node202
        unified_job_template:
          organization:
            name: Default
          name: example-project
          type: project
        related:
          success_nodes: []
          failure_nodes: []
          always_nodes: []
          credentials: []
      - identifier: node301
        all_parents_must_converge: false
        unified_job_template:
          organization:
            name: Default
          name: job template 2
          type: job_template
        related:
          success_nodes: []
          failure_nodes: []
          always_nodes: []
          credentials: []
  register: result

- name: Copy a workflow job template
  workflow_job_template:
    name: copy-workflow
    copy_from: example-workflow
    organization: Foo

- name: Create a workflow job template with schema in template
  awx.awx.workflow_job_template:
    name: example-workflow
    inventory: Demo Inventory
    extra_vars: {'foo': 'bar', 'another-foo': {'barz': 'bar2'}}
    schema:
      - identifier: node101
        unified_job_template:
          name: example-project
          inventory:
            organization:
              name: Default
          type: inventory_source
        related:
          success_nodes: []
          failure_nodes:
            - identifier: node201
          always_nodes: []
          credentials: []
      - identifier: node201
        unified_job_template:
          organization:
            name: Default
          name: job template 1
          type: job_template
        credentials: []
        related:
          success_nodes:
            - identifier: node301
          failure_nodes: []
          always_nodes: []
          credentials: []
      - identifier: node202
        unified_job_template:
          organization:
            name: Default
          name: example-project
          type: project
        related:
          success_nodes: []
          failure_nodes: []
          always_nodes: []
          credentials: []
      - identifier: node301
        all_parents_must_converge: false
        unified_job_template:
          organization:
            name: Default
          name: job template 2
          type: job_template
        related:
          success_nodes: []
          failure_nodes: []
          always_nodes: []
          credentials: []
  register: result

'''

from ..module_utils.controller_api import ControllerAPIModule

import json

response = []

response = []


def update_survey(module, last_request):
    spec_endpoint = last_request.get('related', {}).get('survey_spec')
    if module.params.get('survey_spec') == {}:
        response = module.delete_endpoint(spec_endpoint)
        if response['status_code'] != 200:
            # Not sure how to make this actually return a non 200 to test what to dump in the respinse
            module.fail_json(msg="Failed to delete survey: {0}".format(response['json']))
    else:
        response = module.post_endpoint(spec_endpoint, **{'data': module.params.get('survey_spec')})
        if response['status_code'] != 200:
            module.fail_json(msg="Failed to update survey: {0}".format(response['json']['error']))


def create_schema_nodes(module, response, schema, workflow_id):
    for workflow_node in schema:
        workflow_node_fields = {}
        search_fields = {}
        association_fields = {}

        # Lookup Job Template ID
        if workflow_node['unified_job_template']['name']:
            search_fields = {'name': workflow_node['unified_job_template']['name']}
            if workflow_node['unified_job_template']['type'] is None:
                module.fail_json(msg='Could not find unified job template type in schema {1}'.format(workflow_node))
            if workflow_node['unified_job_template']['type'] == 'inventory_source':
                # workflow_node['unified_job_template']['inventory']:
                organization_id = module.resolve_name_to_id('organizations', workflow_node['unified_job_template']['inventory']['organization']['name'])
                search_fields['organization'] = organization_id
            elif workflow_node['unified_job_template']['type'] == 'workflow_approval':
                pass
            else:
                # workflow_node['unified_job_template']['organization']:
                organization_id = module.resolve_name_to_id('organizations', workflow_node['unified_job_template']['organization']['name'])
                search_fields['organization'] = organization_id
            unified_job_template = module.get_one('unified_job_templates', **{'data': search_fields})
            if unified_job_template:
                workflow_node_fields['unified_job_template'] = unified_job_template['id']
            else:
                if workflow_node['unified_job_template']['type'] != 'workflow_approval':
                    module.fail_json(msg="Unable to Find unified_job_template: {0}".format(search_fields))

        # Lookup Values for other fields

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
            'state',
        ):
            field_val = workflow_node.get(field_name)
            if field_val:
                workflow_node_fields[field_name] = field_val
            if workflow_node['identifier']:
                search_fields = {'identifier': workflow_node['identifier']}

        # Set Search fields
        search_fields['workflow_job_template'] = workflow_node_fields['workflow_job_template'] = workflow_id

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
                    existing_item,
                    workflow_node_fields,
                    endpoint='workflow_job_template_nodes',
                    item_type='workflow_job_template_node',
                    auto_exit=False,
                )
            )
        else:
            # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
            response.append(
                module.delete_if_needed(
                    existing_item,
                    auto_exit=False,
                )
            )

        # Start Approval Node creation process
        if workflow_node['unified_job_template']['type'] == 'workflow_approval':
            for field_name in (
                'name',
                'description',
                'timeout',
            ):
                field_val = workflow_node['unified_job_template'].get(field_name)
                if field_val:
                    workflow_node_fields[field_name] = field_val

            # Attempt to look up an existing item just created
            workflow_job_template_node = module.get_one('workflow_job_template_nodes', **{'data': search_fields})
            workflow_job_template_node_id = workflow_job_template_node['id']
            existing_item = None
            # Due to not able to lookup workflow_approval_templates, find the existing item in another place
            if workflow_job_template_node['related'].get('unified_job_template') is not None:
                existing_item = module.get_endpoint(workflow_job_template_node['related']['unified_job_template'])['json']
            approval_endpoint = 'workflow_job_template_nodes/{0}/create_approval_template/'.format(workflow_job_template_node_id)

            module.create_or_update_if_needed(
                existing_item,
                workflow_node_fields,
                endpoint=approval_endpoint,
                item_type='workflow_job_template_approval_node',
                associations=association_fields,
                auto_exit=False,
            )


def create_schema_nodes_association(module, response, schema, workflow_id):
    for workflow_node in schema:
        workflow_node_fields = {}
        search_fields = {}
        association_fields = {}

        # Set Search fields
        search_fields['workflow_job_template'] = workflow_node_fields['workflow_job_template'] = workflow_id

        # Lookup Values for other fields
        if workflow_node['identifier']:
            workflow_node_fields['identifier'] = workflow_node['identifier']
            search_fields['identifier'] = workflow_node['identifier']

        # Attempt to look up an existing item based on the provided data
        existing_item = module.get_one('workflow_job_template_nodes', **{'data': search_fields})

        if 'state' in workflow_node:
            if workflow_node['state'] == 'absent':
                continue

        if 'related' in workflow_node:
            # Get id's for association fields
            association_fields = {}

            for association in ('always_nodes', 'success_nodes', 'failure_nodes', 'credentials'):
                # Extract out information if it exists
                # Test if it is defined, else move to next association.
                if association in workflow_node['related']:
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
                    if id_list:
                        association_fields[association] = id_list

                    module.create_or_update_if_needed(
                        existing_item,
                        workflow_node_fields,
                        endpoint='workflow_job_template_nodes',
                        item_type='workflow_job_template_node',
                        auto_exit=False,
                        associations=association_fields,
                    )


def destroy_schema_nodes(module, response, workflow_id):
    search_fields = {}

    # Search for existing nodes.
    search_fields['workflow_job_template'] = workflow_id
    existing_items = module.get_all_endpoint('workflow_job_template_nodes', **{'data': search_fields})

    # Loop through found fields
    for workflow_node in existing_items['json']['results']:
        response.append(module.delete_endpoint(workflow_node['url']))


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        copy_from=dict(),
        description=dict(),
        extra_vars=dict(type='dict'),
        organization=dict(),
        survey_spec=dict(type='dict', aliases=['survey']),
        survey_enabled=dict(type='bool'),
        allow_simultaneous=dict(type='bool'),
        ask_variables_on_launch=dict(type='bool'),
        inventory=dict(),
        limit=dict(),
        scm_branch=dict(),
        ask_inventory_on_launch=dict(type='bool'),
        ask_scm_branch_on_launch=dict(type='bool'),
        ask_limit_on_launch=dict(type='bool'),
        webhook_service=dict(choices=['github', 'gitlab']),
        webhook_credential=dict(),
        labels=dict(type="list", elements='str'),
        notification_templates_started=dict(type="list", elements='str'),
        notification_templates_success=dict(type="list", elements='str'),
        notification_templates_error=dict(type="list", elements='str'),
        notification_templates_approvals=dict(type="list", elements='str'),
        schema=dict(type='list', elements='dict'),
        destroy_current_schema=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    copy_from = module.params.get('copy_from')
    state = module.params.get('state')

    # Extract schema parameters
    schema = None
    if module.params.get('schema'):
        schema = module.params.get('schema')
    destroy_current_schema = module.params.get('destroy_current_schema')

    new_fields = {}
    search_fields = {}

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization = module.params.get('organization')
    if organization:
        organization_id = module.resolve_name_to_id('organizations', organization)
        search_fields['organization'] = new_fields['organization'] = organization_id

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('workflow_job_templates', name_or_id=name, **{'data': search_fields})

    # Attempt to look up credential to copy based on the provided name
    if copy_from:
        # a new existing item is formed when copying and is returned.
        existing_item = module.copy_item(
            existing_item,
            copy_from,
            name,
            endpoint='workflow_job_templates',
            item_type='workflow_job_template',
            copy_lookup_data={},
        )

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)

    inventory = module.params.get('inventory')
    if inventory:
        new_fields['inventory'] = module.resolve_name_to_id('inventories', inventory)

    webhook_credential = module.params.get('webhook_credential')
    if webhook_credential:
        new_fields['webhook_credential'] = module.resolve_name_to_id('webhook_credential', webhook_credential)

    # Create the data that gets sent for create and update
    new_fields['name'] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    for field_name in (
        'description',
        'survey_enabled',
        'allow_simultaneous',
        'limit',
        'scm_branch',
        'extra_vars',
        'ask_inventory_on_launch',
        'ask_scm_branch_on_launch',
        'ask_limit_on_launch',
        'ask_variables_on_launch',
        'webhook_service',
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            new_fields[field_name] = field_val

    if 'extra_vars' in new_fields:
        new_fields['extra_vars'] = json.dumps(new_fields['extra_vars'])

    association_fields = {}

    notifications_start = module.params.get('notification_templates_started')
    if notifications_start is not None:
        association_fields['notification_templates_started'] = []
        for item in notifications_start:
            association_fields['notification_templates_started'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_success = module.params.get('notification_templates_success')
    if notifications_success is not None:
        association_fields['notification_templates_success'] = []
        for item in notifications_success:
            association_fields['notification_templates_success'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_error = module.params.get('notification_templates_error')
    if notifications_error is not None:
        association_fields['notification_templates_error'] = []
        for item in notifications_error:
            association_fields['notification_templates_error'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_approval = module.params.get('notification_templates_approvals')
    if notifications_approval is not None:
        association_fields['notification_templates_approvals'] = []
        for item in notifications_approval:
            association_fields['notification_templates_approvals'].append(module.resolve_name_to_id('notification_templates', item))

    labels = module.params.get('labels')
    if labels is not None:
        association_fields['labels'] = []
        for item in labels:
            label_id = module.get_one('labels', name_or_id=item, **{'data': search_fields})
            association_fields['labels'].append(label_id['id'])

    on_change = None
    new_spec = module.params.get('survey_spec')
    if new_spec:
        existing_spec = None
        if existing_item:
            spec_endpoint = existing_item.get('related', {}).get('survey_spec')
            existing_spec = module.get_endpoint(spec_endpoint)['json']
        if new_spec != existing_spec:
            module.json_output['changed'] = True
            if existing_item and module.has_encrypted_values(existing_spec):
                module._encrypted_changed_warning('survey_spec', existing_item, warning=True)
            on_change = update_survey

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item,
        new_fields,
        endpoint='workflow_job_templates',
        item_type='workflow_job_template',
        associations=association_fields,
        on_create=on_change,
        on_update=on_change,
        auto_exit=False,
    )

    # Get Workflow information in case one was just created.
    existing_item = module.get_one('workflow_job_templates', name_or_id=name, **{'data': search_fields})
    workflow_job_template_id = existing_item['id']
    # Destroy current nodes if selected.
    if destroy_current_schema:
        destroy_schema_nodes(module, response, workflow_job_template_id)

    # Work thorugh and lookup value for schema fields
    if schema:
        # Create Schema Nodes
        create_schema_nodes(module, response, schema, workflow_job_template_id)
        # Create Schema Associations
        create_schema_nodes_association(module, response, schema, workflow_job_template_id)
        module.json_output['schema_creation_data'] = response

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
