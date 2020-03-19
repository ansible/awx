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
module: tower_job_template
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower job templates.
description:
    - Create, update, or destroy Ansible Tower job templates. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of this job template.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looed up via the name field.
      required: True
      type: str
    description:
      description:
        - Optional description of this job template.
      required: False
      type: str
      default: ''
    job_type:
      description:
        - The job type to use for the job template.
      required: False
      type: str
      default: 'run'
      choices:
        - 'run'
        - 'check'
        - 'scan'
    inventory:
      description:
        - Name of the inventory to use for the job template.
      required: False
      type: str
    project:
      description:
        - Name of the project to use for the job template.
      required: False
      type: str
    playbook:
      description:
        - Path to the playbook to use for the job template within the project provided.
      required: False
      type: str
      default: ''
    scm_branch:
      description:
        - Branch to use in job run. Project default used if blank. Only allowed if project allow_override field is set to true.
      required: False
      type: str
      default: ''
    forks:
      description:
        - The number of parallel or simultaneous processes to use while executing the playbook.
      required: False
      type: int
      default: '0'
    limit:
      description:
        - A host pattern to further constrain the list of hosts managed or affected by the playbook.
      required: False
      type: str
      default: ''
      aliases:
        - ask_limit
    verbosity:
      description:
        - Control the output level Ansible produces as the playbook runs. 0 - Normal, 1 - Verbose, 2 - More Verbose, 3 - Debug, 4 - Connection Debug.
      required: False
      type: int
      default: 0
      choices:
        - 0
        - 1
        - 2
        - 3
        - 4
        - 5
    extra_vars:
      description:
        - The C(extra_vars) to apply to this job template.
      required: False
      type: dict
      default: {}
      aliases:
        - ask_extra_vars
    job_tags:
      description:
        - Comma separated list of the tags to use for the job template.
      required: False
      type: str
      default: ''
    force_handlers:
      description:
        - Enable forcing playbook handlers to run even if a task fails.
      required: False
      type: bool
      default: 'False'
      aliases:
        - force_handlers_enabled
    skip_tags:
      description:
        - Comma separated list of the tags to skip for the job template.
      required: False
      type: str
      default: ''
    start_at_task:
      description:
        - Start the playbook at the task matching this name.
      required: False
      type: str
      default: ''
    timeout:
      description:
        - The amount of time (in seconds) to run before the task is canceled.
      required: False
      type: int
      default: '0'
    use_fact_cache:
      description:
        - If enabled, Tower will act as an Ansible Fact Cache Plugin; persisting facts at the end of a playbook run to the database and caching facts for use by Ansible.
      required: False
      type: bool
      default: 'False'
      aliases:
        - fact_caching_enabled
    host_config_key:
      description:
        - Allow provisioning callbacks using this host config key.
      required: False
      type: str
      default: ''
    ask_scm_branch_on_launch:
      description:
        - Prompt user for (scm branch) on launch.
      required: False
      type: bool
      default: 'False'
    ask_diff_mode_on_launch:
      description:
        - Prompt user to enable diff mode (show changes) to files when supported by modules.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_diff_mode
    ask_variables_on_launch:
      description:
        - Prompt user for (extra_vars) on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_extra_vars
    ask_limit_on_launch:
      description:
        - Prompt user for a limit on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_limit
    ask_tags_on_launch:
      description:
        - Prompt user for job tags on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_tags
    ask_skip_tags_on_launch:
      description:
        - Prompt user for job tags to skip on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_skip_tags
    ask_job_type_on_launch:
      description:
        - Prompt user for job type on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_job_type
    ask_verbosity_on_launch:
      description:
        - Prompt user to choose a verbosity level on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_verbosity
    ask_inventory_on_launch:
      description:
        - Prompt user for inventory on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_inventory
    ask_credential_on_launch:
      description:
        - Prompt user for credential on launch.
      required: False
      type: bool
      default: 'False'
      aliases:
        - ask_credential
    survey_enabled:
      description:
        - Enable a survey on the job template.
      required: False
      type: bool
      default: 'False'
    become_enabled:
      description:
        - Activate privilege escalation.
      required: False
      type: bool
      default: 'False'
    diff_mode:
      description:
        - If enabled, textual changes made to any templated files on the host are shown in the standard output
      required: False
      type: bool
      default: 'False'
      aliases:
        - diff_mode_enabled
    allow_simultaneous:
      description:
        - Allow simultaneous runs of the job template.
      required: False
      type: bool
      default: 'False'
      aliases:
        - concurrent_jobs_enabled
    custom_virtualenv:
      description:
        - Local absolute file path containing a custom Python virtualenv to use
      required: False
      type: str
      default: ''
    job_slice_count:
      description:
        - The number of jobs to slice into at runtime. Will cause the Job Template to launch a workflow if value is greater than 1.
      required: False
      type: int
      default: '1'
    webhook_service:
      description:
        - Service that webhook requests will be accepted from
      required: False
      type: str
      choices:
        - 'github'
        - 'gitlab'
    webhook_credential:
      description:
        - Personal Access Token for posting back the status to the service API
      required: False
      type: str
    credentials:
      description:
        - The credentials used by this job template
      required: False
      type: list
    labels:
      description:
        - The labels applied to this job template
      required: False
      type: list
    survey_spec:
      description:
        - JSON/YAML dict formatted survey definition.
      required: False
      type: dict
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
      version_added: "3.7"
extends_documentation_fragment: awx.awx.auth
notes:
  - JSON for survey_spec can be found in Tower API Documentation. See
    U(https://docs.ansible.com/ansible-tower/latest/html/towerapi/api_ref.html#/Job_Templates/Job_Templates_job_templates_survey_spec_create)
    for POST operation payload example.
'''

EXAMPLES = '''
'''

from ..module_utils.tower_api import TowerModule

def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, type='str'),
        new_name=dict(required=False, type='str'),
        description=dict(required=False, type='str', default=''),
        job_type=dict(required=False, type='str', choices=['run', 'check', 'scan'], default='run'),
        inventory=dict(required=False, type='str'),
        project=dict(required=False, type='str'),
        playbook=dict(required=False, type='str', default=''),
        scm_branch=dict(required=False, type='str', default=''),
        forks=dict(required=False, type='int', default='0'),
        limit=dict(required=False, type='str', default='', aliases=['ask_limit']),
        verbosity=dict(required=False, type='int', choices=[0, 1, 2, 3, 4, 5], default=0),
        extra_vars=dict(required=False, type='dict', default='{}', aliases=['ask_extra_vars']),
        job_tags=dict(required=False, type='str', default=''),
        force_handlers=dict(required=False, type='bool', default='False', aliases=['force_handlers_enabled']),
        skip_tags=dict(required=False, type='str', default=''),
        start_at_task=dict(required=False, type='str', default=''),
        timeout=dict(required=False, type='int', default='0'),
        use_fact_cache=dict(required=False, type='bool', default='False', aliases=['fact_caching_enabled']),
        host_config_key=dict(required=False, type='str', default=''),
        ask_scm_branch_on_launch=dict(required=False, type='bool', default='False'),
        ask_diff_mode_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_diff_mode']),
        ask_variables_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_extra_vars']),
        ask_limit_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_limit']),
        ask_tags_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_tags']),
        ask_skip_tags_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_skip_tags']),
        ask_job_type_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_job_type']),
        ask_verbosity_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_verbosity']),
        ask_inventory_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_inventory']),
        ask_credential_on_launch=dict(required=False, type='bool', default='False', aliases=['ask_credential']),
        survey_enabled=dict(required=False, type='bool', default='False'),
        become_enabled=dict(required=False, type='bool', default='False'),
        diff_mode=dict(required=False, type='bool', default='False', aliases=['diff_mode_enabled']),
        allow_simultaneous=dict(required=False, type='bool', default='False', aliases=['concurrent_jobs_enabled']),
        custom_virtualenv=dict(required=False, type='str', default=''),
        job_slice_count=dict(required=False, type='int', default='1'),
        webhook_service=dict(required=False, type='str', choices=['github', 'gitlab']),
        webhook_credential=dict(required=False, type='str'),
        credentials=dict(required=False, type="list", default=[]),
        labels=dict(required=False, type="list", default=[]),
        survey_spec=dict(required=False, type="dict"),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    description = module.params.get('description')
    job_type = module.params.get('job_type')
    inventory = module.params.get('inventory')
    project = module.params.get('project')
    playbook = module.params.get('playbook')
    scm_branch = module.params.get('scm_branch')
    forks = module.params.get('forks')
    limit = module.params.get('limit')
    verbosity = module.params.get('verbosity')
    extra_vars = module.params.get('extra_vars')
    job_tags = module.params.get('job_tags')
    force_handlers = module.params.get('force_handlers')
    skip_tags = module.params.get('skip_tags')
    start_at_task = module.params.get('start_at_task')
    timeout = module.params.get('timeout')
    use_fact_cache = module.params.get('use_fact_cache')
    host_config_key = module.params.get('host_config_key')
    ask_scm_branch_on_launch = module.params.get('ask_scm_branch_on_launch')
    ask_diff_mode_on_launch = module.params.get('ask_diff_mode_on_launch')
    ask_variables_on_launch = module.params.get('ask_variables_on_launch')
    ask_limit_on_launch = module.params.get('ask_limit_on_launch')
    ask_tags_on_launch = module.params.get('ask_tags_on_launch')
    ask_skip_tags_on_launch = module.params.get('ask_skip_tags_on_launch')
    ask_job_type_on_launch = module.params.get('ask_job_type_on_launch')
    ask_verbosity_on_launch = module.params.get('ask_verbosity_on_launch')
    ask_inventory_on_launch = module.params.get('ask_inventory_on_launch')
    ask_credential_on_launch = module.params.get('ask_credential_on_launch')
    survey_enabled = module.params.get('survey_enabled')
    become_enabled = module.params.get('become_enabled')
    diff_mode = module.params.get('diff_mode')
    allow_simultaneous = module.params.get('allow_simultaneous')
    custom_virtualenv = module.params.get('custom_virtualenv')
    job_slice_count = module.params.get('job_slice_count')
    webhook_service = module.params.get('webhook_service')
    webhook_credential = module.params.get('webhook_credential')
    survey_spec = module.params.get('survey_spec')
    credentials = module.params.get('credentials')
    labels = module.params.get('labels')
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    inventory_id = None
    if inventory is not None:
        inventory_id = module.resolve_name_to_id('inventories', inventory)
    project_id = None
    if project is not None:
        project_id = module.resolve_name_to_id('projects', project)
    webhook_credential_id = None
    if webhook_credential is not None:
        webhook_credential_id = module.resolve_name_to_id('credentials', webhook_credential)
    credentials_ids = None
    if credentials is not None:
        credentials_ids = []
        for item in credentials:
            credentials_ids.append( module.resolve_name_to_id('credentials', item) )
    label_ids = None
    if labels is not None:
        labels_ids = []
        for item in labels:
            labels_ids.append( module.resolve_name_to_id('labels', item) )

    # Pull in additional posts
    additional_posts = []
    if survey_spec is not None:
        additional_posts.append({
            'endpoint_reference': 'survey_spec',
            'data': survey_spec,
        })

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('job_templates', **{
        'data': {
            'name': name,
        }
    })

    # Create the data that gets sent for create and update
    new_fields = {}
    new_fields['name'] = new_name if new_name else name
    if description is not None:
        new_fields['description'] = description
    if job_type is not None:
        new_fields['job_type'] = job_type
    if inventory is not None:
        new_fields['inventory'] = inventory_id
    if project is not None:
        new_fields['project'] = project_id
    if playbook is not None:
        new_fields['playbook'] = playbook
    if scm_branch is not None:
        new_fields['scm_branch'] = scm_branch
    if forks is not None:
        new_fields['forks'] = forks
    if limit is not None:
        new_fields['limit'] = limit
    if verbosity is not None:
        new_fields['verbosity'] = verbosity
    if extra_vars is not None:
        new_fields['extra_vars'] = extra_vars
    if job_tags is not None:
        new_fields['job_tags'] = job_tags
    if force_handlers is not None:
        new_fields['force_handlers'] = force_handlers
    if skip_tags is not None:
        new_fields['skip_tags'] = skip_tags
    if start_at_task is not None:
        new_fields['start_at_task'] = start_at_task
    if timeout is not None:
        new_fields['timeout'] = timeout
    if use_fact_cache is not None:
        new_fields['use_fact_cache'] = use_fact_cache
    if host_config_key is not None:
        new_fields['host_config_key'] = host_config_key
    if ask_scm_branch_on_launch is not None:
        new_fields['ask_scm_branch_on_launch'] = ask_scm_branch_on_launch
    if ask_diff_mode_on_launch is not None:
        new_fields['ask_diff_mode_on_launch'] = ask_diff_mode_on_launch
    if ask_variables_on_launch is not None:
        new_fields['ask_variables_on_launch'] = ask_variables_on_launch
    if ask_limit_on_launch is not None:
        new_fields['ask_limit_on_launch'] = ask_limit_on_launch
    if ask_tags_on_launch is not None:
        new_fields['ask_tags_on_launch'] = ask_tags_on_launch
    if ask_skip_tags_on_launch is not None:
        new_fields['ask_skip_tags_on_launch'] = ask_skip_tags_on_launch
    if ask_job_type_on_launch is not None:
        new_fields['ask_job_type_on_launch'] = ask_job_type_on_launch
    if ask_verbosity_on_launch is not None:
        new_fields['ask_verbosity_on_launch'] = ask_verbosity_on_launch
    if ask_inventory_on_launch is not None:
        new_fields['ask_inventory_on_launch'] = ask_inventory_on_launch
    if ask_credential_on_launch is not None:
        new_fields['ask_credential_on_launch'] = ask_credential_on_launch
    if survey_enabled is not None:
        new_fields['survey_enabled'] = survey_enabled
    if become_enabled is not None:
        new_fields['become_enabled'] = become_enabled
    if diff_mode is not None:
        new_fields['diff_mode'] = diff_mode
    if allow_simultaneous is not None:
        new_fields['allow_simultaneous'] = allow_simultaneous
    if custom_virtualenv is not None:
        new_fields['custom_virtualenv'] = custom_virtualenv
    if job_slice_count is not None:
        new_fields['job_slice_count'] = job_slice_count
    if webhook_service is not None:
        new_fields['webhook_service'] = webhook_service
    if webhook_credential is not None:
        new_fields['webhook_credential'] = webhook_credential_id

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
            additional_posts=additional_posts,
        )



if __name__ == '__main__':
    main()
