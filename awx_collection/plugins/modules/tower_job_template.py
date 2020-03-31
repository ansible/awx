#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_job_template
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower job templates.
description:
    - Create, update, or destroy Ansible Tower job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the job template.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looed up via the name field.
      type: str
    description:
      description:
        - Description to use for the job template.
      type: str
    job_type:
      description:
        - The job type to use for the job template.
      required: False
      choices: ["run", "check"]
      type: str
    inventory:
      description:
        - Name of the inventory to use for the job template.
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
      version_added: 2.7
      type: str
    credentials:
      description:
        - List of credentials to use for the job template.
      type: list
      elements: str
      version_added: 2.8
      default: []
    vault_credential:
      description:
        - Name of the vault credential to use for the job template.
        - Deprecated, use 'credentials'.
      version_added: 2.7
      type: str
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
      version_added: 3.7
    job_tags:
      description:
        - Comma separated list of the tags to use for the job template.
      type: str
    force_handlers:
      description:
        - Enable forcing playbook handlers to run even if a task fails.
      version_added: 2.7
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
      version_added: 2.7
      type: str
    diff_mode:
      description:
        - Enable diff mode for the job template.
      version_added: 2.7
      type: bool
      aliases:
        - diff_mode_enabled
      default: 'no'
    use_fact_cache:
      description:
        - Enable use of fact caching for the job template.
      version_added: 2.7
      type: bool
      default: 'no'
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
      default: 'False'
    ask_diff_mode_on_launch:
      description:
        - Prompt user to enable diff mode (show changes) to files when supported by modules.
      version_added: 2.7
      type: bool
      default: 'False'
      aliases:
        - ask_diff_mode
    ask_variables_on_launch:
      description:
        - Prompt user for (extra_vars) on launch.
      type: bool
      default: 'False'
      aliases:
        - ask_extra_vars
    ask_limit_on_launch:
      description:
        - Prompt user for a limit on launch.
      version_added: 2.7
      type: bool
      default: 'False'
      aliases:
        - ask_limit
    ask_tags_on_launch:
      description:
        - Prompt user for job tags on launch.
      type: bool
      default: 'False'
      aliases:
        - ask_tags
    ask_skip_tags_on_launch:
      description:
        - Prompt user for job tags to skip on launch.
      version_added: 2.7
      type: bool
      default: 'False'
      aliases:
        - ask_skip_tags
    ask_job_type_on_launch:
      description:
        - Prompt user for job type on launch.
      type: bool
      default: 'False'
      aliases:
        - ask_job_type
    ask_verbosity_on_launch:
      description:
        - Prompt user to choose a verbosity level on launch.
      version_added: 2.7
      type: bool
      default: 'False'
      aliases:
        - ask_verbosity
    ask_inventory_on_launch:
      description:
        - Prompt user for inventory on launch.
      type: bool
      default: 'False'
      aliases:
        - ask_inventory
    ask_credential_on_launch:
      description:
        - Prompt user for credential on launch.
      type: bool
      default: 'False'
      aliases:
        - ask_credential
    survey_enabled:
      description:
        - Enable a survey on the job template.
      version_added: 2.7
      type: bool
      default: 'no'
    survey_spec:
      description:
        - JSON/YAML dict formatted survey definition.
      version_added: 2.8
      type: dict
    become_enabled:
      description:
        - Activate privilege escalation.
      type: bool
      default: 'no'
    allow_simultaneous:
      description:
        - Allow simultaneous runs of the job template.
      version_added: 2.7
      type: bool
      default: 'no'
      aliases:
        - concurrent_jobs_enabled
    timeout:
      description:
        - Maximum time in seconds to wait for a job to finish (server-side).
      type: int
    custom_virtualenv:
      version_added: "2.9"
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
      type: str
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
      type: list
      elements: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      type: str
      version_added: "3.7"

extends_documentation_fragment: awx.awx.auth

notes:
  - JSON for survey_spec can be found in Tower API Documentation. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/api_ref.html#/Job_Templates/Job_Templates_job_templates_survey_spec_create)
    for POST operation payload example.
'''


EXAMPLES = '''
- name: Create tower Ping job template
  tower_job_template:
    name: "Ping"
    job_type: "run"
    inventory: "Local"
    project: "Demo"
    playbook: "ping.yml"
    credentials:
      - "Local"
    state: "present"
    tower_config_file: "~/tower_cli.cfg"
    survey_enabled: yes
    survey_spec: "{{ lookup('file', 'my_survey.json') }}"
    custom_virtualenv: "/var/lib/awx/venv/custom-venv/"
'''

from ..module_utils.tower_api import TowerModule
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
        description=dict(default=''),
        job_type=dict(choices=['run', 'check']),
        inventory=dict(),
        project=dict(),
        playbook=dict(),
        credential=dict(default=''),
        vault_credential=dict(default=''),
        custom_virtualenv=dict(required=False),
        credentials=dict(type='list', default=[], elements='str'),
        forks=dict(type='int'),
        limit=dict(default=''),
        verbosity=dict(type='int', choices=[0, 1, 2, 3, 4], default=0),
        extra_vars=dict(type='dict', required=False),
        job_tags=dict(default=''),
        force_handlers=dict(type='bool', default=False, aliases=['force_handlers_enabled']),
        skip_tags=dict(default=''),
        start_at_task=dict(default=''),
        timeout=dict(type='int', default=0),
        use_fact_cache=dict(type='bool', aliases=['fact_caching_enabled']),
        host_config_key=dict(),
        ask_diff_mode_on_launch=dict(type='bool', aliases=['ask_diff_mode']),
        ask_variables_on_launch=dict(type='bool', aliases=['ask_extra_vars']),
        ask_limit_on_launch=dict(type='bool', aliases=['ask_limit']),
        ask_tags_on_launch=dict(type='bool', aliases=['ask_tags']),
        ask_skip_tags_on_launch=dict(type='bool', aliases=['ask_skip_tags']),
        ask_job_type_on_launch=dict(type='bool', aliases=['ask_job_type']),
        ask_verbosity_on_launch=dict(type='bool', aliases=['ask_verbosity']),
        ask_inventory_on_launch=dict(type='bool', aliases=['ask_inventory']),
        ask_credential_on_launch=dict(type='bool', aliases=['ask_credential']),
        survey_enabled=dict(type='bool'),
        survey_spec=dict(type="dict"),
        become_enabled=dict(type='bool'),
        diff_mode=dict(type='bool', aliases=['diff_mode_enabled']),
        allow_simultaneous=dict(type='bool', aliases=['concurrent_jobs_enabled']),
        scm_branch=dict(),
        ask_scm_branch_on_launch=dict(type='bool'),
        job_slice_count=dict(type='int', default='1'),
        webhook_service=dict(choices=['github', 'gitlab']),
        webhook_credential=dict(),
        labels=dict(type="list", elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
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

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('job_templates', **{
        'data': {
            'name': name,
        }
    })

    # Create the data that gets sent for create and update
    new_fields = {}
    new_fields['name'] = new_name if new_name else name
    for field_name in (
        'description', 'job_type', 'playbook', 'scm_branch', 'forks', 'limit', 'verbosity',
        'job_tags', 'force_handlers', 'skip_tags', 'start_at_task', 'timeout', 'use_fact_cache',
        'host_config_key', 'ask_scm_branch_on_launch', 'ask_diff_mode_on_launch', 'ask_variables_on_launch',
        'ask_limit_on_launch', 'ask_tags_on_launch', 'ask_skip_tags_on_launch', 'ask_job_type_on_launch',
        'ask_verbosity_on_launch', 'ask_inventory_on_launch', 'ask_credential_on_launch', 'survey_enabled',
        'become_enabled', 'diff_mode', 'allow_simultaneous', 'custom_virtualenv', 'job_slice_count', 'webhook_service',
    ):
        field_val = module.params.get(field_name)
        if field_val:
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
        new_fields['project'] = module.resolve_name_to_id('projects', project)
    if webhook_credential is not None:
        new_fields['webhook_credential'] = module.resolve_name_to_id('credentials', webhook_credential)

    credentials_ids = None
    if credentials is not None:
        credentials_ids = []
        for item in credentials:
            credentials_ids.append(module.resolve_name_to_id('credentials', item))

    labels = module.params.get('labels')
    labels_ids = None
    if labels is not None:
        labels_ids = []
        for item in labels:
            labels_ids.append(module.resolve_name_to_id('labels', item))

    on_change = None
    new_spec = module.params.get('survey_spec')
    if new_spec is not None:
        existing_spec = None
        if existing_item:
            spec_endpoint = existing_item.get('related', {}).get('survey_spec')
            existing_spec = module.get_endpoint(spec_endpoint)['json']
        if new_spec != existing_spec:
            module.json_output['changed'] = True
            on_change = update_survey

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)
    elif state == 'present':
        # If the state was present and we can let the module build or update the existing item, this will return on its own
        module.create_or_update_if_needed(
            existing_item, new_fields,
            endpoint='job_templates', item_type='job_template',
            associations={
                'credentials': credentials_ids,
                'labels': labels_ids,
            },
            on_create=on_change, on_update=on_change,
        )


if __name__ == '__main__':
    main()
