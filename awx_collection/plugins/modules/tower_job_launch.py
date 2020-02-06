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
module: tower_job_launch
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: Launch an Ansible Job.
description:
    - Launch an Ansible Tower jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of the job template to use.
      required: True
      type: str
      aliases: ['job_template']
    job_type:
      description:
        - Job_type to use for the job, only used if prompt for job_type is set.
      choices: ["run", "check"]
      type: str
    inventory:
      description:
        - Inventory to use for the job, only used if prompt for inventory is set.
      type: str
    credentials:
      description:
        - Credential to use for job, only used if prompt for credential is set.
      type: list
      aliases: ['credential']
    extra_vars:
      description:
        - extra_vars to use for the Job Template. Prepend C(@) if a file.
        - ask_extra_vars needs to be set to True via tower_job_template module
          when creating the Job Template.
      type: dict
    limit:
      description:
        - Limit to use for the I(job_template).
      type: str
    tags:
      description:
        - Specific tags to use for from playbook.
      type: list
    scm_branch:
      description:
        - A specific of the SCM project to run the template on.
        - This is only applicable if your project allows for branch override.
      type: str
    skip_tags:
      description:
        - Specific tags to skip from the playbook.
      type: list
    verbosity:
      description:
        - Verbosity level for this job run
      type: int
      choices: [ 0, 1, 2, 3, 4, 5 ]
    diff_mode:
      description:
        - Show the changes made by Ansible tasks where supported
      type: bool
    credential_passwords:
      description:
        - Passwords for credentials which are set to prompt on launch
      type: dict
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
# Launch a job template
- name: Launch a job
  tower_job_launch:
    job_template: "My Job Template"
  register: job

- name: Wait for job max 120s
  tower_job_wait:
    job_id: "{{ job.id }}"
    timeout: 120

- name: Launch a job template with extra_vars on remote Tower instance
  tower_job_launch:
    job_template: "My Job Template"
    extra_vars:
      var1: "My First Variable"
      var2: "My Second Variable"
      var3: "My Third Variable"
    job_type: run

# Launch job template with inventory and credential for prompt on launch
- name: Launch a job with inventory and credential
  tower_job_launch:
    job_template: "My Job Template"
    inventory: "My Inventory"
    credential: "My Credential"
  register: job
- name: Wait for job max 120s
  tower_job_wait:
    job_id: "{{ job.id }}"
    timeout: 120
'''

RETURN = '''
id:
    description: job id of the newly launched job
    returned: success
    type: int
    sample: 86
status:
    description: status of newly launched job
    returned: success
    type: str
    sample: pending
'''

from ..module_utils.tower_api import TowerModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(type='str', required=True, aliases=['job_template']),
        job_type=dict(type='str', choices=['run', 'check']),
        inventory=dict(type='str', default=None),
        # Credentials will be a str instead of a list for backwards compatability
        credentials=dict(type='list', default=None, aliases=['credential']),
        limit=dict(),
        tags=dict(type='list'),
        extra_vars=dict(type='dict', required=False),
        scm_branch=dict(type='str', required=False),
        skip_tags=dict(type='list', required=False),
        verbosity=dict(type='int', required=False, choices=[0, 1, 2, 3, 4, 5]),
        diff_mode=dict(type='bool', required=False),
        credential_passwords=dict(type='dict', required=False),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    optional_args = {}
    # Extract our parameters
    name = module.params.get('name')
    optional_args['job_type'] = module.params.get('job_type')
    inventory = module.params.get('inventory')
    credentials = module.params.get('credentials')
    optional_args['limit'] = module.params.get('limit')
    optional_args['tags'] = module.params.get('tags')
    optional_args['extra_vars'] = module.params.get('extra_vars')
    optional_args['scm_branch'] = module.params.get('scm_branch')
    optional_args['skip_tags'] = module.params.get('skip_tags')
    optional_args['verbosity'] = module.params.get('verbosity')
    optional_args['diff_mode'] = module.params.get('diff_mode')
    optional_args['credential_passwords'] = module.params.get('credential_passwords')

    # Create a datastructure to pass into our job launch
    post_data = {}
    for key in optional_args.keys():
        if optional_args[key]:
            post_data[key] = optional_args[key]

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if inventory:
        post_data['inventory'] = module.resolve_name_to_id('inventories', inventory)

    if credentials:
        post_data['credentials'] = []
        for credential in credentials:
            post_data['credentials'].append(module.resolve_name_to_id('credentials', credential))

    # Attempt to look up job_template based on the provided name
    job_template = module.get_one('job_templates', **{
        'data': {
            'name': name,
        }
    })

    if job_template is None:
        module.fail_json(msg="Unable to find job template by name {0}".format(name))

    # The API will allow you to submit values to a jb launch that are not prompt on launch.
    # Therefore, we will test to see if anything is set which is not prompt on launch and fail.
    check_vars_to_prompts = {
        'scm_branch': 'ask_scm_branch_on_launch',
        'diff_mode': 'ask_diff_mode_on_launch',
        'extra_vars': 'ask_variables_on_launch',
        'limit': 'ask_limit_on_launch',
        'tags': 'ask_tags_on_launch',
        'skip_tags': 'ask_skip_tags_on_launch',
        'job_type': 'ask_job_type_on_launch',
        'verbosity': 'ask_verbosity_on_launch',
        'inventory': 'ask_inventory_on_launch',
        'credentials': 'ask_credential_on_launch',
    }

    param_errors = []
    for variable_name in check_vars_to_prompts:
        if module.params.get(variable_name) and not job_template[check_vars_to_prompts[variable_name]]:
            param_errors.append("The field {0} was specified but the job template does not allow for it to be overridden".format(variable_name))
    if len(param_errors) > 0:
        module.fail_json(msg="Parameters specified which can not be passed into job template, see errors for details", **{'errors': param_errors})

    # Launch the job
    results = module.post_endpoint(job_template['related']['launch'], **{'data': post_data})

    if results['status_code'] != 201:
        module.fail_json(msg="Failed to launch job, see response for details", **{'response': results})

    module.exit_json(**{
        'changed': True,
        'id': results['json']['id'],
        'status': results['json']['status'],
    })


if __name__ == '__main__':
    main()
