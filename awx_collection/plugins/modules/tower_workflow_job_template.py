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
module: tower_workflow_job_template
author: "John Westcott IV (@john-westcott-iv)"
short_description: create, update, or destroy Ansible Tower workflow job templates.
description:
    - Create, update, or destroy Ansible Tower workflow job templates.
    - Replaces the deprecated tower_workflow_template module.
    - Use the tower_workflow_job_template_node after this to build the workflow's graph.
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
    survey:
      description:
        - The definition of the survey associated to the workflow.
      type: dict
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
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Create a workflow job template
  tower_workflow_job_template:
    name: example-workflow
    description: created by Ansible Playbook
    organization: Default
'''

from ..module_utils.tower_api import TowerAPIModule

import json


def update_survey(module, last_request):
    spec_endpoint = last_request.get('related', {}).get('survey_spec')
    module.post_endpoint(spec_endpoint, **{'data': module.params.get('survey')})
    module.exit_json(**module.json_output)


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        extra_vars=dict(type='dict'),
        organization=dict(),
        survey=dict(type='dict'),  # special handling
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
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    state = module.params.get('state')

    new_fields = {}
    search_fields = {}

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization = module.params.get('organization')
    if organization:
        organization_id = module.resolve_name_to_id('organizations', organization)
        search_fields['organization'] = new_fields['organization'] = organization_id

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('workflow_job_templates', name_or_id=name, **{'data': search_fields})

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
            'description', 'survey_enabled', 'allow_simultaneous',
            'limit', 'scm_branch', 'extra_vars',
            'ask_inventory_on_launch', 'ask_scm_branch_on_launch', 'ask_limit_on_launch', 'ask_variables_on_launch',
            'webhook_service',):
        field_val = module.params.get(field_name)
        if field_val:
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
            association_fields['labels'].append(module.resolve_name_to_id('labels', item))
# Code to use once Issue #7567 is resolved
#            search_fields = {'name': item}
#            if organization:
#                search_fields['organization'] = organization_id
#            label_id = module.get_one('labels', **{'data': search_fields})
#            association_fields['labels'].append(label_id)

    on_change = None
    new_spec = module.params.get('survey')
    if new_spec:
        existing_spec = None
        if existing_item:
            spec_endpoint = existing_item.get('related', {}).get('survey_spec')
            existing_spec = module.get_endpoint(spec_endpoint)
        if new_spec != existing_spec:
            module.json_output['changed'] = True
            if existing_item and module.has_encrypted_values(existing_spec):
                module._encrypted_changed_warning('survey_spec', existing_item, warning=True)
            on_change = update_survey

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(
        existing_item, new_fields,
        endpoint='workflow_job_templates', item_type='workflow_job_template',
        associations=association_fields,
        on_create=on_change, on_update=on_change
    )


if __name__ == '__main__':
    main()
