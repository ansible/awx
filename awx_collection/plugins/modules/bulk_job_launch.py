#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: bulk_job_launch
author: "Seth Foster (@fosterseth)"
short_description: Bulk job launch in Automation Platform Controller
description:
    - Single-request bulk job launch in Automation Platform Controller.
    - Creates a workflow where each node corresponds to an item specified in the jobs option.
    - Any options specified at the top level will inherited by the launched jobs (if prompt on launch is enabled for those fields).
    - Provides a way to submit many jobs at once to Controller.
options:
    jobs:
      description:
        - List of jobs to create.
      required: True
      type: list
      elements: dict
      suboptions:
        unified_job_template:
          description:
            - Job template ID to use when launching.
          type: int
          required: True
        inventory:
          description:
            - Inventory ID applied as a prompt, if job template prompts for inventory
          type: int
        execution_environment:
          description:
            - Execution environment ID applied as a prompt, if job template prompts for execution environments
          type: int
        instance_groups:
          description:
            - Instance group IDs applied as a prompt, if job template prompts for instance groups
          type: list
          elements: int
        credentials:
          description:
            - Credential IDs applied as a prompt, if job template prompts for credentials
          type: list
          elements: int
        labels:
          description:
            - Label IDs to use for the job, if job template prompts for labels
          type: list
          elements: int
        extra_data:
          description:
            - Extra variables to apply at launch time, if job template prompts for extra variables
          type: dict
          default: {}
        diff_mode:
          description:
            - Show the changes made by Ansible tasks where supported
          type: bool
        verbosity:
          description:
            - Verbosity level for this ad hoc command run
          type: int
          choices: [ 0, 1, 2, 3, 4, 5 ]
        scm_branch:
          description:
            - SCM branch applied as a prompt, if job template prompts for SCM branch
            - This is only applicable if the project allows for branch override
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
            - Tags to skip, applied as a prompt, if job template prompts for job tags
          type: str
        limit:
          description:
            - Limit to act on, applied as a prompt, if job template prompts for limit
          type: str
        forks:
          description:
            - The number of parallel or simultaneous processes to use while executing the playbook, if job template prompts for forks
          type: int
        job_slice_count:
          description:
            - The number of jobs to slice into at runtime, if job template prompts for job slices.
            - Will cause the Job Template to launch a workflow if value is greater than 1.
          type: int
          default: '1'
        identifier:
          description:
            - Identifier for the resulting workflow node that represents this job
          type: str
        timeout:
          description:
            - Maximum time in seconds to wait for a job to finish (server-side), if job template prompts for timeout.
          type: int
    name:
      description:
        - The name of the bulk job that is created
      required: False
      type: str
    description:
      description:
        - Optional description of this bulk job.
      type: str
    organization:
      description:
        - If not provided, will use the organization the user is in.
        - Required if the user belongs to more than one organization.
        - Affects who can see the resulting bulk job.
      type: str
    inventory:
      description:
        - Inventory name, ID, or named URL to use for the jobs ran within the bulk job, only used if prompt for inventory is set.
      type: str
    scm_branch:
      description:
        - A specific branch of the SCM project to run the template on.
        - This is only applicable if the project allows for branch override.
      type: str
    extra_vars:
      description:
        - Any extra vars required to launch the job.
        - Extends the extra_data field at the individual job level.
      type: dict
    limit:
      description:
        - Limit to use for the bulk job.
      type: str
    job_tags:
      description:
        - A comma-separated list of playbook tags to specify what parts of the playbooks should be executed.
      type: str
    skip_tags:
      description:
        - A comma-separated list of playbook tags to skip certain tasks or parts of the playbooks to be executed.
      type: str
    wait:
      description:
        - Wait for the bulk job to complete.
      default: True
      type: bool
    interval:
      description:
        - The interval to request an update from the controller.
      required: False
      default: 2
      type: float
extends_documentation_fragment: awx.awx.auth
'''

RETURN = '''
job_info:
    description: dictionary containing information about the bulk job executed
    returned: If bulk job launched
    type: dict
'''

EXAMPLES = '''
- name: Launch bulk jobs
  bulk_job_launch:
    name: My Bulk Job Launch
    jobs:
      - unified_job_template: 7
        skip_tags: foo
      - unified_job_template: 10
        limit: foo
        extra_data:
          food: carrot
          color: orange
    limit: bar
    credentials:
      - "My Credential"
      - "suplementary cred"
    extra_vars: # these override / extend extra_data at the job level
      food: grape
      animal: owl
    organization: Default
    inventory: Demo Inventory

- name: Launch bulk jobs with lookup plugin
  bulk_job_launch:
    name: My Bulk Job Launch
    jobs:
      - unified_job_template: 7
      - unified_job_template: "{{ lookup('awx.awx.controller_api', 'job_templates', query_params={'name': 'Demo Job Template'},
        return_ids=True, expect_one=True) }}"
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        jobs=dict(required=True, type='list', elements='dict'),
        name=dict(),
        description=dict(),
        organization=dict(type='str'),
        inventory=dict(type='str'),
        limit=dict(),
        scm_branch=dict(),
        extra_vars=dict(type='dict'),
        job_tags=dict(),
        skip_tags=dict(),
        wait=dict(required=False, default=True, type='bool'),
        interval=dict(required=False, default=2.0, type='float'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    post_data_names = (
        'jobs',
        'name',
        'description',
        'limit',
        'scm_branch',
        'extra_vars',
        'job_tags',
        'skip_tags',
    )
    post_data = {}
    for p in post_data_names:
        val = module.params.get(p)
        if val:
            post_data[p] = val

    # Resolve name to ID for related resources
    # Do not resolve name for "jobs" suboptions, for optimization
    org_name = module.params.get('organization')
    if org_name:
        post_data['organization'] = module.resolve_name_to_id('organizations', org_name)

    inv_name = module.params.get('inventory')
    if inv_name:
        post_data['inventory'] = module.resolve_name_to_id('inventories', inv_name)

    # Extract our parameters
    wait = module.params.get('wait')
    timeout = module.params.get('timeout')
    interval = module.params.get('interval')
    name = module.params.get('name')

    # Launch the jobs
    result = module.post_endpoint("bulk/job_launch", data=post_data)

    if result['status_code'] != 201:
        module.fail_json(msg="Failed to launch bulk jobs, see response for details", response=result)

    module.json_output['changed'] = True
    module.json_output['id'] = result['json']['id']
    module.json_output['status'] = result['json']['status']
    # This is for backwards compatability
    module.json_output['job_info'] = result['json']

    if not wait:
        module.exit_json(**module.json_output)

    # Invoke wait function
    module.wait_on_url(url=result['json']['url'], object_name=name, object_type='Bulk Job Launch', timeout=timeout, interval=interval)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
