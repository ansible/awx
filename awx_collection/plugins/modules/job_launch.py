#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: job_launch
author: "Wayne Witzel III (@wwitzel3)"
short_description: Launch an Ansible Job.
description:
    - Launch an Automation Platform Controller jobs. See
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
    organization:
      description:
        - Organization the job template exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
    credentials:
      description:
        - Credential to use for job, only used if prompt for credential is set.
      type: list
      aliases: ['credential']
      elements: str
    extra_vars:
      description:
        - extra_vars to use for the Job Template.
        - ask_extra_vars needs to be set to True via job_template module
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
      elements: str
    scm_branch:
      description:
        - A specific of the SCM project to run the template on.
        - This is only applicable if your project allows for branch override.
      type: str
    skip_tags:
      description:
        - Specific tags to skip from the playbook.
      type: list
      elements: str
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
    execution_environment:
      description:
        - Execution environment to use for the job, only used if prompt for execution environment is set.
      type: str
    forks:
      description:
        - Forks to use for the job, only used if prompt for forks is set.
      type: int
    instance_groups:
      description:
        - Instance groups to use for the job, only used if prompt for instance groups is set.
      type: list
      elements: str
    job_slice_count:
      description:
        - Job slice count to use for the job, only used if prompt for job slice count is set.
      type: int
    labels:
      description:
        - Labels to use for the job, only used if prompt for labels is set.
      type: list
      elements: str
    job_timeout:
      description:
        - Timeout to use for the job, only used if prompt for timeout is set.
        - This parameter is sent through the API to the job.
      type: int
    wait:
      description:
        - Wait for the job to complete.
      default: False
      type: bool
    interval:
      description:
        - The interval to request an update from the controller.
      required: False
      default: 2
      type: float
    timeout:
      description:
        - If waiting for the job to complete this will abort after this
          amount of seconds. This happens on the module side.
      type: int
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Launch a job
  job_launch:
    job_template: "My Job Template"
  register: job

- name: Launch a job template with extra_vars on remote controller instance
  job_launch:
    job_template: "My Job Template"
    extra_vars:
      var1: "My First Variable"
      var2: "My Second Variable"
      var3: "My Third Variable"
    job_type: run

- name: Launch a job with inventory and credential
  job_launch:
    job_template: "My Job Template"
    inventory: "My Inventory"
    credential: "My Credential"
  register: job
- name: Wait for job max 120s
  job_wait:
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

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, aliases=['job_template']),
        job_type=dict(choices=['run', 'check']),
        inventory=dict(default=None),
        organization=dict(),
        # Credentials will be a str instead of a list for backwards compatability
        credentials=dict(type='list', default=None, aliases=['credential'], elements='str'),
        limit=dict(),
        tags=dict(type='list', elements='str'),
        extra_vars=dict(type='dict'),
        scm_branch=dict(),
        skip_tags=dict(type='list', elements='str'),
        verbosity=dict(type='int', choices=[0, 1, 2, 3, 4, 5]),
        diff_mode=dict(type='bool'),
        credential_passwords=dict(type='dict', no_log=False),
        execution_environment=dict(),
        forks=dict(type='int'),
        instance_groups=dict(type='list', elements='str'),
        job_slice_count=dict(type='int'),
        labels=dict(type='list', elements='str'),
        job_timeout=dict(type='int'),
        wait=dict(default=False, type='bool'),
        interval=dict(default=2.0, type='float'),
        timeout=dict(default=None, type='int'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    optional_args = {}
    # Extract our parameters
    name = module.params.get('name')
    inventory = module.params.get('inventory')
    organization = module.params.get('organization')
    credentials = module.params.get('credentials')
    execution_environment = module.params.get('execution_environment')
    instance_groups = module.params.get('instance_groups')
    labels = module.params.get('labels')
    wait = module.params.get('wait')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')

    for field_name in (
        'job_type',
        'limit',
        'extra_vars',
        'scm_branch',
        'verbosity',
        'diff_mode',
        'credential_passwords',
        'forks',
        'job_slice_count',
        'job_timeout',
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            optional_args[field_name] = field_val

        # Special treatment of tags parameters
        job_tags = module.params.get('tags')
        if job_tags is not None:
            optional_args['job_tags'] = ",".join(job_tags)
        skip_tags = module.params.get('skip_tags')
        if skip_tags is not None:
            optional_args['skip_tags'] = ",".join(skip_tags)

    # job_timeout is special because its actually timeout but we already had a timeout variable
    job_timeout = module.params.get('job_timeout')
    if job_timeout is not None:
        optional_args['timeout'] = job_timeout

    # Create a datastructure to pass into our job launch
    post_data = {}
    for arg_name, arg_value in optional_args.items():
        if arg_value:
            post_data[arg_name] = arg_value

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if inventory:
        post_data['inventory'] = module.resolve_name_to_id('inventories', inventory)
    if execution_environment:
        post_data['execution_environment'] = module.resolve_name_to_id('execution_environments', execution_environment)

    if credentials:
        post_data['credentials'] = []
        for credential in credentials:
            post_data['credentials'].append(module.resolve_name_to_id('credentials', credential))
    if labels:
        post_data['labels'] = []
        for label in labels:
            post_data['labels'].append(module.resolve_name_to_id('labels', label))
    if instance_groups:
        post_data['instance_groups'] = []
        for instance_group in instance_groups:
            post_data['instance_groups'].append(module.resolve_name_to_id('instance_groups', instance_group))

    # Attempt to look up job_template based on the provided name
    lookup_data = {}
    if organization:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    job_template = module.get_one('job_templates', name_or_id=name, data=lookup_data)

    if job_template is None:
        module.fail_json(msg="Unable to find job template by name {0}".format(name))

    # The API will allow you to submit values to a jb launch that are not prompt on launch.
    # Therefore, we will test to see if anything is set which is not prompt on launch and fail.
    check_vars_to_prompts = {
        'scm_branch': 'ask_scm_branch_on_launch',
        'diff_mode': 'ask_diff_mode_on_launch',
        'limit': 'ask_limit_on_launch',
        'tags': 'ask_tags_on_launch',
        'skip_tags': 'ask_skip_tags_on_launch',
        'job_type': 'ask_job_type_on_launch',
        'verbosity': 'ask_verbosity_on_launch',
        'inventory': 'ask_inventory_on_launch',
        'credentials': 'ask_credential_on_launch',
    }

    param_errors = []
    for variable_name, prompt in check_vars_to_prompts.items():
        if module.params.get(variable_name) and not job_template[prompt]:
            param_errors.append("The field {0} was specified but the job template does not allow for it to be overridden".format(variable_name))
    # Check if Either ask_variables_on_launch, or survey_enabled is enabled for use of extra vars.
    if module.params.get('extra_vars') and not (job_template['ask_variables_on_launch'] or job_template['survey_enabled']):
        param_errors.append("The field extra_vars was specified but the job template does not allow for it to be overridden")
    if len(param_errors) > 0:
        module.fail_json(msg="Parameters specified which can not be passed into job template, see errors for details", **{'errors': param_errors})

    # Launch the job
    results = module.post_endpoint(job_template['related']['launch'], **{'data': post_data})

    if results['status_code'] != 201:
        module.fail_json(msg="Failed to launch job, see response for details", **{'response': results})

    if not wait:
        module.exit_json(
            **{
                'changed': True,
                'id': results['json']['id'],
                'status': results['json']['status'],
            }
        )

    # Invoke wait function
    results = module.wait_on_url(url=results['json']['url'], object_name=name, object_type='Job', timeout=timeout, interval=interval)

    module.exit_json(
        **{
            'changed': True,
            'id': results['json']['id'],
            'status': results['json']['status'],
        }
    )


if __name__ == '__main__':
    main()
