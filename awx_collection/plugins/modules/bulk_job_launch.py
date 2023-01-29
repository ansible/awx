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
    - The result is flat workflow, each job specified in the parameter jobs results in a workflow job node.
    - Any options specified at the top level will inherited by the launched jobs (if prompt on launch is enabled for those fields).
    - Designed to efficiently start many jobs at once.
options:
    jobs:
      description:
        - List of jobs to create.
        - Any promptable field on unified_job_template can be provided as a field on the list item (e.g. limit).
      required: True
      type: list
    name:
      description:
        - The name of the bulk job that is created
      required: False
      type: str
    organization:
      description:
        - If not provided, will use the organization the user is in.
        - Required if the user belongs to more than one organization.
        - Affects who can see the resulting bulk job.
      type: str
    inventory:
      description:
        - Inventory to use for the jobs ran within the bulk job, only used if prompt for inventory is set.
      type: str
    limit:
      description:
        - Limit to use for the I(job_template).
      type: str
    scm_branch:
      description:
        - A specific branch of the SCM project to run the template on.
        - This is only applicable if your project allows for branch override.
      type: str
    extra_vars:
      description:
        - Any extra vars required to launch the job.
      type: dict
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
        - Wait for the workflow to complete.
      default: True
      type: bool
    interval:
      description:
        - The interval to request an update from the controller.
      required: False
      default: 2
      type: float
    timeout:
      description:
        - If waiting for the workflow to complete this will abort after this
          amount of seconds
      type: int
extends_documentation_fragment: awx.awx.auth
'''

RETURN = '''
job_info:
    description: dictionary containing information about the workflow executed
    returned: If workflow launched
    type: dict
'''


EXAMPLES = '''
- name: Launch bulk jobs
  bulk_job_launch:
    name: My Bulk Job Launch
    jobs:
      - unified_job_template: 7
      - unified_job_template: 10
        limit: foo
    limit: bar
    inventory: 1 # only affects job templates with prompt on launch enabled for inventory

- name: Launch bulk jobs with lookup plugin
  bulk_job_launch:
    name: My Bulk Job Launch
    jobs:
      - unified_job_template: 7
      - unified_job_template: "{{ lookup('awx.awx.controller_api', 'job_templates', query_params={'name': 'Demo Job Template'}, return_ids=True) }}"
'''

from ..module_utils.controller_api import ControllerAPIModule
import json

def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        jobs=dict(required=True, type='list'),
        name=dict(),
        organization=dict(),
        inventory=dict(),
        limit=dict(),
        scm_branch=dict(),
        extra_vars=dict(type='dict'),
        job_tags=dict(),
        skip_tags=dict(),
        wait=dict(required=False, default=True, type='bool'),
        interval=dict(required=False, default=2.0, type='float'),
        timeout=dict(required=False, default=None, type='int'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    wait = module.params.get('wait')
    timeout = module.params.get('timeout')
    interval = module.params.get('interval')
    jobs = module.params.get('jobs')

    # Launch the jobs
    result = module.post_endpoint("bulk/job_launch", data={"jobs": jobs})

    if result['status_code'] != 201:
        module.fail_json(msg="Failed to launch bulk jobs, see response for details", response=result)

    module.json_output['changed'] = True
    module.json_output['id'] = result['json']['id']
    module.json_output['status'] = result['json']['status']
    # This is for backwards compatability
    module.json_output['job_info'] = {'id': result['json']['id']}

    if not wait:
        module.exit_json(**module.json_output)

    # Invoke wait function
    module.wait_on_url(url=result['json']['url'], object_name=name, object_type='Bulk Job Launch', timeout=timeout, interval=interval)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()