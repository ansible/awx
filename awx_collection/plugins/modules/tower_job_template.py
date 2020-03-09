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
    scm_branch:
      description:
        - Branch to use in job run. Project default used if blank. Only allowed if project allow_override field is set to true.
      required: False
      type: str
      default: ''
    ask_tags_on_launch:
      required: False
      type: bool
      default: 'False'
    job_type:
      required: False
      type: str
      default: 'run'
      choices:
        - 'run'
        - 'check'
        - 'scan'
    skip_tags:
      required: False
      type: str
      default: ''
    ask_verbosity_on_launch:
      required: False
      type: bool
      default: 'False'
    playbook:
      required: False
      type: str
      default: ''
    survey_enabled:
      required: False
      type: bool
      default: 'False'
    description:
      description:
        - Optional description of this job template.
      required: False
      type: str
      default: ''
    ask_diff_mode_on_launch:
      required: False
      type: bool
      default: 'False'
    job_tags:
      required: False
      type: str
      default: ''
    allow_simultaneous:
      required: False
      type: bool
      default: 'False'
    diff_mode:
      description:
        - If enabled, textual changes made to any templated files on the host are shown in the standard output
      required: False
      type: bool
      default: 'False'
    ask_inventory_on_launch:
      required: False
      type: bool
      default: 'False'
    inventory:
      required: False
      type: str
    limit:
      required: False
      type: str
      default: ''
    forks:
      required: False
      type: int
      default: '0'
    become_enabled:
      required: False
      type: bool
      default: 'False'
    force_handlers:
      required: False
      type: bool
      default: 'False'
    ask_variables_on_launch:
      required: False
      type: bool
      default: 'False'
    ask_job_type_on_launch:
      required: False
      type: bool
      default: 'False'
    start_at_task:
      required: False
      type: str
      default: ''
    ask_limit_on_launch:
      required: False
      type: bool
      default: 'False'
    webhook_credential:
      description:
        - Personal Access Token for posting back the status to the service API
      required: False
      type: str
    custom_virtualenv:
      description:
        - Local absolute file path containing a custom Python virtualenv to use
      required: False
      type: str
      default: ''
    host_config_key:
      required: False
      type: str
      default: ''
    job_slice_count:
      description:
        - The number of jobs to slice into at runtime. Will cause the Job Template to launch a workflow if value is greater than 1.
      required: False
      type: int
      default: '1'
    ask_skip_tags_on_launch:
      required: False
      type: bool
      default: 'False'
    name:
      description:
        - Name of this job template.
      required: True
      type: str
    new_name:
      description:
        - To use when changing a team's name.
      required: True
      type: str
    use_fact_cache:
      description:
        - If enabled, Tower will act as an Ansible Fact Cache Plugin; persisting facts at the end of a playbook run to the database and caching facts for use by Ansible.
      required: False
      type: bool
      default: 'False'
    extra_vars:
      required: False
      type: dict
      default: ''
    verbosity:
      required: False
      type: str
      default: '0'
      choices:
        - '0'
        - '1'
        - '2'
        - '3'
        - '4'
        - '5'
    ask_credential_on_launch:
      required: False
      type: bool
      default: 'False'
    project:
      required: False
      type: str
    webhook_service:
      description:
        - Service that webhook requests will be accepted from
      required: False
      type: str
      choices:
        - 'github'
        - 'gitlab'
    timeout:
      description:
        - The amount of time (in seconds) to run before the task is canceled.
      required: False
      type: int
      default: '0'
    ask_scm_branch_on_launch:
      required: False
      type: bool
      default: 'False'
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
'''

from ..module_utils.tower_api import TowerModule

def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        scm_branch=dict( required=False, type='str', default='',),
        ask_tags_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_tags']),
        job_type=dict( required=False, type='str', choices=[ 'run', 'check', 'scan', ], default='run',),
        skip_tags=dict( required=False, type='str', default='',),
        ask_verbosity_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_verbosity']),
        playbook=dict( required=False, type='str', default='',),
        survey_enabled=dict( required=False, type='bool', default='False',),
        description=dict( required=False, type='str', default='',),
        ask_diff_mode_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_diff_mode']),
        job_tags=dict( required=False, type='str', default='',),
        allow_simultaneous=dict( required=False, type='bool', default='False', aliases=['concurrent_jobs_enabled']),
        diff_mode=dict( required=False, type='bool', default='False', aliases=['diff_mode_enabled']),
        ask_inventory_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_inventory']),
        inventory=dict( required=False, type='str',),
        limit=dict( required=False, type='str', default='', aliases=['ask_limit']),
        forks=dict( required=False, type='int', default='0',),
        become_enabled=dict( required=False, type='bool', default='False',),
        force_handlers=dict( required=False, type='bool', default='False', aliases=['force_handlers_enabled']),
        ask_variables_on_launch=dict( required=False, type='bool', default='False',),
        ask_job_type_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_job_type']),
        start_at_task=dict( required=False, type='str', default='',),
        ask_limit_on_launch=dict( required=False, type='bool', default='False',),
        webhook_credential=dict( required=False, type='str',),
        custom_virtualenv=dict( required=False, type='str', default='',),
        host_config_key=dict( required=False, type='str', default='',),
        job_slice_count=dict( required=False, type='int', default='1',),
        ask_skip_tags_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_skip_tags']),
        name=dict( required=True, type='str',),
        new_name=dict(required=False, type='str'),
        use_fact_cache=dict( required=False, type='bool', default='False', aliases=['fact_caching_enabled']),
        extra_vars=dict( required=False, type='dict', default={}, aliases=['ask_extra_vars']),
        verbosity=dict( required=False, type='str', choices=[ '0', '1', '2', '3', '4', '5', ], default='0',),
        ask_credential_on_launch=dict( required=False, type='bool', default='False', aliases=['ask_credential']),
        project=dict( required=False, type='str',),
        webhook_service=dict( required=False, type='str', choices=[ 'github', 'gitlab', ],),
        timeout=dict( required=False, type='int', default='0',),
        ask_scm_branch_on_launch=dict( required=False, type='bool', default='False',),
        state=dict(choices=['present', 'absent'], default='present'),
        credentials=dict(required=False, type='list', default=[])
#SURVEY_SPEC
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    # Extract our parameters
    scm_branch = module.params.get('scm_branch')
    if len(scm_branch) > 1024:
        module.fail_msg(msg="The value for scm_branch can not be longer than 1024")
    ask_tags_on_launch = module.params.get('ask_tags_on_launch')
    job_type = module.params.get('job_type')
    skip_tags = module.params.get('skip_tags')
    if len(skip_tags) > 1024:
        module.fail_msg(msg="The value for skip_tags can not be longer than 1024")
    ask_verbosity_on_launch = module.params.get('ask_verbosity_on_launch')
    playbook = module.params.get('playbook')
    if len(playbook) > 1024:
        module.fail_msg(msg="The value for playbook can not be longer than 1024")
    survey_enabled = module.params.get('survey_enabled')
    description = module.params.get('description')
    ask_diff_mode_on_launch = module.params.get('ask_diff_mode_on_launch')
    job_tags = module.params.get('job_tags')
    if len(job_tags) > 1024:
        module.fail_msg(msg="The value for job_tags can not be longer than 1024")
    allow_simultaneous = module.params.get('allow_simultaneous')
    diff_mode = module.params.get('diff_mode')
    ask_inventory_on_launch = module.params.get('ask_inventory_on_launch')
    inventory = module.params.get('inventory')
    limit = module.params.get('limit')
    forks = module.params.get('forks')
    if forks < 0:
        module.fail_msg(msg="The value for forks can not be less than 0")
    if forks > 2147483647:
        module.fail_msg(msg="The value for forks can not be larger than 2147483647")
    become_enabled = module.params.get('become_enabled')
    force_handlers = module.params.get('force_handlers')
    ask_variables_on_launch = module.params.get('ask_variables_on_launch')
    ask_job_type_on_launch = module.params.get('ask_job_type_on_launch')
    start_at_task = module.params.get('start_at_task')
    if len(start_at_task) > 1024:
        module.fail_msg(msg="The value for start_at_task can not be longer than 1024")
    ask_limit_on_launch = module.params.get('ask_limit_on_launch')
    webhook_credential = module.params.get('webhook_credential')
    custom_virtualenv = module.params.get('custom_virtualenv')
    if len(custom_virtualenv) > 100:
        module.fail_msg(msg="The value for custom_virtualenv can not be longer than 100")
    host_config_key = module.params.get('host_config_key')
    if len(host_config_key) > 1024:
        module.fail_msg(msg="The value for host_config_key can not be longer than 1024")
    job_slice_count = module.params.get('job_slice_count')
    if job_slice_count < 0:
        module.fail_msg(msg="The value for job_slice_count can not be less than 0")
    if job_slice_count > 2147483647:
        module.fail_msg(msg="The value for job_slice_count can not be larger than 2147483647")
    ask_skip_tags_on_launch = module.params.get('ask_skip_tags_on_launch')
    name = module.params.get('name')
    if len(name) > 512:
        module.fail_msg(msg="The value for name can not be longer than 512")
    new_name = module.params.get("new_name")
    use_fact_cache = module.params.get('use_fact_cache')
    extra_vars = module.params.get('extra_vars')
    verbosity = module.params.get('verbosity')
    ask_credential_on_launch = module.params.get('ask_credential_on_launch')
    project = module.params.get('project')
    webhook_service = module.params.get('webhook_service')
    timeout = module.params.get('timeout')
    if timeout < -2147483648:
        module.fail_msg(msg="The value for timeout can not be less than -2147483648")
    if timeout > 2147483647:
        module.fail_msg(msg="The value for timeout can not be larger than 2147483647")
    ask_scm_branch_on_launch = module.params.get('ask_scm_branch_on_launch')
    state = module.params.get('state')
    credentials = module.params.get('credentials')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    inventory_id = None
    if inventory:
        inventory_id = module.resolve_name_to_id('inventory', inventory)
    webhook_credential_id = None
    if webhook_credential:
        webhook_credential_id = module.resolve_name_to_id('webhook_credential', webhook_credential)
    project_id = None
    if project:
        project_id = module.resolve_name_to_id('project', project)
    credential_ids = None
    if credentials:
        credential_ids = []
        for credential in credentials:
            credential_ids.append( module.resolve_name_to_id('credentials', credential) )

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('job_templates', **{
        'data': {
            'name': name,
        }
    })

    # Create the data that gets sent for create and update
    new_fields = {}
    if scm_branch:
        new_fields['scm_branch'] = scm_branch
    if ask_tags_on_launch:
        new_fields['ask_tags_on_launch'] = ask_tags_on_launch
    if job_type:
        new_fields['job_type'] = job_type
    if skip_tags:
        new_fields['skip_tags'] = skip_tags
    if ask_verbosity_on_launch:
        new_fields['ask_verbosity_on_launch'] = ask_verbosity_on_launch
    if playbook:
        new_fields['playbook'] = playbook
    if survey_enabled:
        new_fields['survey_enabled'] = survey_enabled
    if description:
        new_fields['description'] = description
    if ask_diff_mode_on_launch:
        new_fields['ask_diff_mode_on_launch'] = ask_diff_mode_on_launch
    if job_tags:
        new_fields['job_tags'] = job_tags
    if allow_simultaneous:
        new_fields['allow_simultaneous'] = allow_simultaneous
    if diff_mode:
        new_fields['diff_mode'] = diff_mode
    if ask_inventory_on_launch:
        new_fields['ask_inventory_on_launch'] = ask_inventory_on_launch
    if inventory:
        new_fields['inventory'] = inventory_id
    if limit:
        new_fields['limit'] = limit
    if forks:
        new_fields['forks'] = forks
    if become_enabled:
        new_fields['become_enabled'] = become_enabled
    if force_handlers:
        new_fields['force_handlers'] = force_handlers
    if ask_variables_on_launch:
        new_fields['ask_variables_on_launch'] = ask_variables_on_launch
    if ask_job_type_on_launch:
        new_fields['ask_job_type_on_launch'] = ask_job_type_on_launch
    if start_at_task:
        new_fields['start_at_task'] = start_at_task
    if ask_limit_on_launch:
        new_fields['ask_limit_on_launch'] = ask_limit_on_launch
    if webhook_credential:
        new_fields['webhook_credential'] = webhook_credential_id
    if custom_virtualenv:
        new_fields['custom_virtualenv'] = custom_virtualenv
    if host_config_key:
        new_fields['host_config_key'] = host_config_key
    if job_slice_count:
        new_fields['job_slice_count'] = job_slice_count
    if ask_skip_tags_on_launch:
        new_fields['ask_skip_tags_on_launch'] = ask_skip_tags_on_launch
    new_fields['name'] = new_name if new_name else name
    if use_fact_cache:
        new_fields['use_fact_cache'] = use_fact_cache
    if extra_vars:
        new_fields['extra_vars'] = extra_vars
    if verbosity:
        new_fields['verbosity'] = verbosity
    if ask_credential_on_launch:
        new_fields['ask_credential_on_launch'] = ask_credential_on_launch
    if project:
        new_fields['project'] = project_id
    if webhook_service:
        new_fields['webhook_service'] = webhook_service
    if timeout:
        new_fields['timeout'] = timeout
    if ask_scm_branch_on_launch:
        new_fields['ask_scm_branch_on_launch'] = ask_scm_branch_on_launch

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)
    elif state == 'present':
        # If the state was present and we can let the module build or update the existing item, this will return on its own
        module.create_or_update_if_needed(existing_item, new_fields, endpoint='job_templates', item_type='job_template', associations={ 'credentials': credential_ids })


if __name__ == '__main__':
    main()

