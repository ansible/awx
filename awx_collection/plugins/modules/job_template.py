#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: job_template
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller job templates.
description:
    - Create, update, or destroy Automation Platform Controller job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the job template.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      type: str
    copy_from:
      description:
        - Name or id to copy the job template from.
        - This will copy an existing job template and change any parameters supplied.
        - The new job template name will be the one provided in the name parameter.
        - The organization parameter is not used in this, to facilitate copy from one organization to another.
        - Provide the id or use the lookup plugin to provide the id if multiple job templates share the same name.
      type: str
    description:
      description:
        - Description to use for the job template.
      type: str
    job_type:
      description:
        - The job type to use for the job template.
      choices: ["run", "check"]
      type: str
    inventory:
      description:
        - Name of the inventory to use for the job template.
      type: str
    organization:
      description:
        - Organization the job template exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - The Organization is inferred from the associated project
        - If not provided, will lookup by name only, which does not work with duplicates.
        - Requires Automation Platform Version 3.7.0 or AWX 10.0.0 IS NOT backwards compatible with earlier versions.
      type: str
    project:
      description:
        - Name of the project to use for the job template.
      type: str
    playbook:
      description:
        - Path to the playbook to use for the job template within the project provided.
      type: str
    credential:
      description:
        - Name of the credential to use for the job template.
        - Deprecated, use 'credentials'.
      type: str
    credentials:
      description:
        - List of credentials to use for the job template.
      type: list
      elements: str
    vault_credential:
      description:
        - Name of the vault credential to use for the job template.
        - Deprecated, use 'credentials'.
      type: str
    execution_environment:
      description:
        - Execution Environment to use for the JT.
      type: str
    custom_virtualenv:
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
        - Only compatible with older versions of AWX/Tower
        - Deprecated, will be removed in the future
      type: str
    instance_groups:
      description:
        - list of Instance Groups for this Organization to run on.
      type: list
      elements: str
    forks:
      description:
        - The number of parallel or simultaneous processes to use while executing the playbook.
      type: int
    limit:
      description:
        - A host pattern to further constrain the list of hosts managed or affected by the playbook
      type: str
    verbosity:
      description:
        - Control the output level Ansible produces as the playbook runs. 0 - Normal, 1 - Verbose, 2 - More Verbose, 3 - Debug, 4 - Connection Debug.
      choices: [0, 1, 2, 3, 4]
      default: 0
      type: int
    extra_vars:
      description:
        - Specify C(extra_vars) for the template.
      type: dict
    job_tags:
      description:
        - Comma separated list of the tags to use for the job template.
      type: str
    force_handlers:
      description:
        - Enable forcing playbook handlers to run even if a task fails.
      type: bool
      default: 'no'
      aliases:
        - force_handlers_enabled
    skip_tags:
      description:
        - Comma separated list of the tags to skip for the job template.
      type: str
    start_at_task:
      description:
        - Start the playbook at the task matching this name.
      type: str
    diff_mode:
      description:
        - Enable diff mode for the job template.
      type: bool
      aliases:
        - diff_mode_enabled
    use_fact_cache:
      description:
        - Enable use of fact caching for the job template.
      type: bool
      aliases:
        - fact_caching_enabled
    host_config_key:
      description:
        - Allow provisioning callbacks using this host config key.
      type: str
    ask_scm_branch_on_launch:
      description:
        - Prompt user for (scm branch) on launch.
      type: bool
    ask_diff_mode_on_launch:
      description:
        - Prompt user to enable diff mode (show changes) to files when supported by modules.
      type: bool
      aliases:
        - ask_diff_mode
    ask_variables_on_launch:
      description:
        - Prompt user for (extra_vars) on launch.
      type: bool
      aliases:
        - ask_extra_vars
    ask_limit_on_launch:
      description:
        - Prompt user for a limit on launch.
      type: bool
      aliases:
        - ask_limit
    ask_tags_on_launch:
      description:
        - Prompt user for job tags on launch.
      type: bool
      aliases:
        - ask_tags
    ask_skip_tags_on_launch:
      description:
        - Prompt user for job tags to skip on launch.
      type: bool
      aliases:
        - ask_skip_tags
    ask_job_type_on_launch:
      description:
        - Prompt user for job type on launch.
      type: bool
      aliases:
        - ask_job_type
    ask_verbosity_on_launch:
      description:
        - Prompt user to choose a verbosity level on launch.
      type: bool
      aliases:
        - ask_verbosity
    ask_inventory_on_launch:
      description:
        - Prompt user for inventory on launch.
      type: bool
      aliases:
        - ask_inventory
    ask_credential_on_launch:
      description:
        - Prompt user for credential on launch.
      type: bool
      aliases:
        - ask_credential
    ask_execution_environment_on_launch:
      description:
        - Prompt user for execution environment on launch.
      type: bool
      aliases:
        - ask_execution_environment
    ask_forks_on_launch:
      description:
        - Prompt user for forks on launch.
      type: bool
      aliases:
        - ask_forks
    ask_instance_groups_on_launch:
      description:
        - Prompt user for instance groups on launch.
      type: bool
      aliases:
        - ask_instance_groups
    ask_job_slice_count_on_launch:
      description:
        - Prompt user for job slice count on launch.
      type: bool
      aliases:
        - ask_job_slice_count
    ask_labels_on_launch:
      description:
        - Prompt user for labels on launch.
      type: bool
      aliases:
        - ask_labels
    ask_timeout_on_launch:
      description:
        - Prompt user for timeout on launch.
      type: bool
      aliases:
        - ask_timeout
    survey_enabled:
      description:
        - Enable a survey on the job template.
      type: bool
    survey_spec:
      description:
        - JSON/YAML dict formatted survey definition.
      type: dict
    become_enabled:
      description:
        - Activate privilege escalation.
      type: bool
    allow_simultaneous:
      description:
        - Allow simultaneous runs of the job template.
      type: bool
      aliases:
        - concurrent_jobs_enabled
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish (server-side).
      type: int
    job_slice_count:
      description:
        - The number of jobs to slice into at runtime. Will cause the Job Template to launch a workflow if value is greater than 1.
      type: int
      default: '1'
    webhook_service:
      description:
        - Service that webhook requests will be accepted from
      type: str
      choices:
        - ''
        - 'github'
        - 'gitlab'
    webhook_credential:
      description:
        - Personal Access Token for posting back the status to the service API
      type: str
    scm_branch:
      description:
        - Branch to use in job run. Project default used if blank. Only allowed if project allow_override field is set to true.
      type: str
      default: ''
    labels:
      description:
        - The labels applied to this job template
        - Must be created with the labels module first. This will error if the label has not been created.
      type: list
      elements: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
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
    prevent_instance_group_fallback:
      description:
        - Prevent falling back to instance groups set on the associated inventory or organization
      type: bool

extends_documentation_fragment: awx.awx.auth

notes:
  - JSON for survey_spec can be found in the API Documentation. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/api_ref.html#/Job_Templates/Job_Templates_job_templates_survey_spec_create)
    for POST operation payload example.
'''


EXAMPLES = '''
- name: Create Ping job template
  job_template:
    name: "Ping"
    job_type: "run"
    organization: "Default"
    inventory: "Local"
    project: "Demo"
    playbook: "ping.yml"
    credentials:
      - "Local"
    state: "present"
    controller_config_file: "~/tower_cli.cfg"
    survey_enabled: yes
    survey_spec: "{{ lookup('file', 'my_survey.json') }}"

- name: Add start notification to Job Template
  job_template:
    name: "Ping"
    notification_templates_started:
      - Notification1
      - Notification2

- name: Remove Notification1 start notification from Job Template
  job_template:
    name: "Ping"
    notification_templates_started:
      - Notification2

- name: Copy Job Template
  job_template:
    name: copy job template
    copy_from: test job template
    job_type: "run"
    inventory: Copy Foo Inventory
    project: test
    playbook: hello_world.yml
    state: "present"
'''

from ..module_utils.controller_api import ControllerAPIModule
import json


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
    module.exit_json(**module.json_output)


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        copy_from=dict(),
        description=dict(),
        organization=dict(),
        job_type=dict(choices=['run', 'check']),
        inventory=dict(),
        project=dict(),
        playbook=dict(),
        credential=dict(),
        vault_credential=dict(),
        credentials=dict(type='list', elements='str'),
        execution_environment=dict(),
        custom_virtualenv=dict(),
        instance_groups=dict(type="list", elements='str'),
        forks=dict(type='int'),
        limit=dict(),
        verbosity=dict(type='int', choices=[0, 1, 2, 3, 4], default=0),
        extra_vars=dict(type='dict'),
        job_tags=dict(),
        force_handlers=dict(type='bool', default=False, aliases=['force_handlers_enabled']),
        skip_tags=dict(),
        start_at_task=dict(),
        timeout=dict(type='int', default=0),
        use_fact_cache=dict(type='bool', aliases=['fact_caching_enabled']),
        host_config_key=dict(no_log=False),
        ask_diff_mode_on_launch=dict(type='bool', aliases=['ask_diff_mode']),
        ask_variables_on_launch=dict(type='bool', aliases=['ask_extra_vars']),
        ask_limit_on_launch=dict(type='bool', aliases=['ask_limit']),
        ask_tags_on_launch=dict(type='bool', aliases=['ask_tags']),
        ask_skip_tags_on_launch=dict(type='bool', aliases=['ask_skip_tags']),
        ask_job_type_on_launch=dict(type='bool', aliases=['ask_job_type']),
        ask_verbosity_on_launch=dict(type='bool', aliases=['ask_verbosity']),
        ask_inventory_on_launch=dict(type='bool', aliases=['ask_inventory']),
        ask_credential_on_launch=dict(type='bool', aliases=['ask_credential']),
        ask_execution_environment_on_launch=dict(type='bool', aliases=['ask_execution_environment']),
        ask_forks_on_launch=dict(type='bool', aliases=['ask_forks']),
        ask_instance_groups_on_launch=dict(type='bool', aliases=['ask_instance_groups']),
        ask_job_slice_count_on_launch=dict(type='bool', aliases=['ask_job_slice_count']),
        ask_labels_on_launch=dict(type='bool', aliases=['ask_labels']),
        ask_timeout_on_launch=dict(type='bool', aliases=['ask_timeout']),
        survey_enabled=dict(type='bool'),
        survey_spec=dict(type="dict"),
        become_enabled=dict(type='bool'),
        diff_mode=dict(type='bool', aliases=['diff_mode_enabled']),
        allow_simultaneous=dict(type='bool', aliases=['concurrent_jobs_enabled']),
        scm_branch=dict(),
        ask_scm_branch_on_launch=dict(type='bool'),
        job_slice_count=dict(type='int', default='1'),
        webhook_service=dict(choices=['github', 'gitlab', '']),
        webhook_credential=dict(),
        labels=dict(type="list", elements='str'),
        notification_templates_started=dict(type="list", elements='str'),
        notification_templates_success=dict(type="list", elements='str'),
        notification_templates_error=dict(type="list", elements='str'),
        prevent_instance_group_fallback=dict(type="bool"),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    copy_from = module.params.get('copy_from')
    state = module.params.get('state')

    # Deal with legacy credential and vault_credential
    credential = module.params.get('credential')
    vault_credential = module.params.get('vault_credential')
    credentials = module.params.get('credentials')
    if vault_credential:
        if credentials is None:
            credentials = []
        credentials.append(vault_credential)
    if credential:
        if credentials is None:
            credentials = []
        credentials.append(credential)

    new_fields = {}
    search_fields = {}

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization_id = None
    organization = module.params.get('organization')
    if organization:
        organization_id = module.resolve_name_to_id('organizations', organization)
        search_fields['organization'] = new_fields['organization'] = organization_id

    ee = module.params.get('execution_environment')
    if ee:
        new_fields['execution_environment'] = module.resolve_name_to_id('execution_environments', ee)

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('job_templates', name_or_id=name, **{'data': search_fields})

    # Attempt to look up credential to copy based on the provided name
    if copy_from:
        # a new existing item is formed when copying and is returned.
        existing_item = module.copy_item(
            existing_item,
            copy_from,
            name,
            endpoint='job_templates',
            item_type='job_template',
            copy_lookup_data={},
        )

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)

    # Create the data that gets sent for create and update
    new_fields['name'] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    for field_name in (
        'description',
        'job_type',
        'playbook',
        'scm_branch',
        'forks',
        'limit',
        'verbosity',
        'job_tags',
        'force_handlers',
        'skip_tags',
        'start_at_task',
        'timeout',
        'use_fact_cache',
        'host_config_key',
        'ask_scm_branch_on_launch',
        'ask_diff_mode_on_launch',
        'ask_variables_on_launch',
        'ask_limit_on_launch',
        'ask_tags_on_launch',
        'ask_skip_tags_on_launch',
        'ask_job_type_on_launch',
        'ask_verbosity_on_launch',
        'ask_inventory_on_launch',
        'ask_credential_on_launch',
        'ask_execution_environment_on_launch',
        'ask_forks_on_launch',
        'ask_instance_groups_on_launch',
        'ask_job_slice_count_on_launch',
        'ask_labels_on_launch',
        'ask_timeout_on_launch',
        'survey_enabled',
        'become_enabled',
        'diff_mode',
        'allow_simultaneous',
        'custom_virtualenv',
        'job_slice_count',
        'webhook_service',
        'prevent_instance_group_fallback',
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            new_fields[field_name] = field_val

    # Special treatment of extra_vars parameter
    extra_vars = module.params.get('extra_vars')
    if extra_vars is not None:
        new_fields['extra_vars'] = json.dumps(extra_vars)

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    inventory = module.params.get('inventory')
    project = module.params.get('project')
    webhook_credential = module.params.get('webhook_credential')

    if inventory is not None:
        new_fields['inventory'] = module.resolve_name_to_id('inventories', inventory)
    if project is not None:
        if organization_id is not None:
            project_data = module.get_one(
                'projects',
                name_or_id=project,
                **{
                    'data': {
                        'organization': organization_id,
                    }
                }
            )
            if project_data is None:
                module.fail_json(msg="The project {0} in organization {1} was not found on the controller instance server".format(project, organization))
            new_fields['project'] = project_data['id']
        else:
            new_fields['project'] = module.resolve_name_to_id('projects', project)
    if webhook_credential is not None:
        new_fields['webhook_credential'] = module.resolve_name_to_id('credentials', webhook_credential)

    association_fields = {}

    if credentials is not None:
        association_fields['credentials'] = []
        for item in credentials:
            association_fields['credentials'].append(module.resolve_name_to_id('credentials', item))

    labels = module.params.get('labels')
    if labels is not None:
        association_fields['labels'] = []
        for item in labels:
            label_id = module.get_one('labels', name_or_id=item, **{'data': search_fields})
            if label_id is None:
                module.fail_json(msg='Could not find label entry with name {0}'.format(item))
            else:
                association_fields['labels'].append(label_id['id'])

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

    instance_group_names = module.params.get('instance_groups')
    if instance_group_names is not None:
        association_fields['instance_groups'] = []
        for item in instance_group_names:
            association_fields['instance_groups'].append(module.resolve_name_to_id('instance_groups', item))

    on_change = None
    new_spec = module.params.get('survey_spec')
    if new_spec is not None:
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
        endpoint='job_templates',
        item_type='job_template',
        associations=association_fields,
        on_create=on_change,
        on_update=on_change,
    )


if __name__ == '__main__':
    main()
