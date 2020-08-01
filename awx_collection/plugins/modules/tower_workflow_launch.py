#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_workflow_launch
author: "John Westcott IV (@john-westcott-iv)"
short_description: Run a workflow in Ansible Tower
description:
    - Launch an Ansible Tower workflows. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name of the workflow template to run.
      required: True
      type: str
      aliases:
        - workflow_template
    organization:
      description:
        - Organization the workflow job template exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
    inventory:
      description:
        - Inventory to use for the job ran with this workflow, only used if prompt for inventory is set.
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
    wait:
      description:
        - Wait for the workflow to complete.
      default: True
      type: bool
    interval:
      description:
        - The interval to request an update from Tower.
      required: False
      default: 1
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
- name: Launch a workflow with a timeout of 10 seconds
  tower_workflow_launch:
    workflow_template: "Test Workflow"
    timeout: 10

- name: Launch a Workflow with extra_vars without waiting
  tower_workflow_launch:
    workflow_template: "Test workflow"
    extra_vars:
      var1: My First Variable
      var2: My Second Variable
    wait: False
'''

from ..module_utils.tower_api import TowerModule
import json
import time


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, aliases=['workflow_template']),
        organization=dict(),
        inventory=dict(),
        limit=dict(),
        scm_branch=dict(),
        extra_vars=dict(type='dict'),
        wait=dict(required=False, default=True, type='bool'),
        interval=dict(required=False, default=1.0, type='float'),
        timeout=dict(required=False, default=None, type='int'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    optional_args = {}
    # Extract our parameters
    name = module.params.get('name')
    organization = module.params.get('organization')
    inventory = module.params.get('inventory')
    optional_args['limit'] = module.params.get('limit')
    wait = module.params.get('wait')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')

    # Special treatment of extra_vars parameter
    extra_vars = module.params.get('extra_vars')
    if extra_vars is not None:
        optional_args['extra_vars'] = json.dumps(extra_vars)

    # Create a datastructure to pass into our job launch
    post_data = {}
    for key in optional_args.keys():
        if optional_args[key]:
            post_data[key] = optional_args[key]

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if inventory:
        post_data['inventory'] = module.resolve_name_to_id('inventories', inventory)

    # Attempt to look up job_template based on the provided name
    lookup_data = {'name': name}
    if organization:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    workflow_job_template = module.get_one('workflow_job_templates', data=lookup_data)

    if workflow_job_template is None:
        module.fail_json(msg="Unable to find workflow job template")

    # The API will allow you to submit values to a jb launch that are not prompt on launch.
    # Therefore, we will test to see if anything is set which is not prompt on launch and fail.
    check_vars_to_prompts = {
        'inventory': 'ask_inventory_on_launch',
        'limit': 'ask_limit_on_launch',
        'scm_branch': 'ask_scm_branch_on_launch',
        'extra_vars': 'ask_variables_on_launch',
    }

    param_errors = []
    for variable_name in check_vars_to_prompts:
        if variable_name in post_data and not workflow_job_template[check_vars_to_prompts[variable_name]]:
            param_errors.append("The field {0} was specified but the workflow job template does not allow for it to be overridden".format(variable_name))
    if len(param_errors) > 0:
        module.fail_json(msg="Parameters specified which can not be passed into wotkflow job template, see errors for details", errors=param_errors)

    # Launch the job
    result = module.post_endpoint(workflow_job_template['related']['launch'], data=post_data)

    if result['status_code'] != 201:
        module.fail_json(msg="Failed to launch workflow, see response for details", response=result)

    module.json_output['changed'] = True
    module.json_output['id'] = result['json']['id']
    module.json_output['status'] = result['json']['status']
    # This is for backwards compatability
    module.json_output['job_info'] = {'id': result['json']['id']}

    if not wait:
        module.exit_json(**module.json_output)

    # Grab our start time to compare against for the timeout
    start = time.time()

    job_url = result['json']['url']
    while not result['json']['finished']:
        # If we are past our time out fail with a message
        if timeout and timeout < time.time() - start:
            module.json_output['msg'] = "Monitoring aborted due to timeout"
            module.fail_json(**module.json_output)

        # Put the process to sleep for our interval
        time.sleep(interval)

        result = module.get_endpoint(job_url)
        module.json_output['status'] = result['json']['status']

    # If the job has failed, we want to raise a task failure for that so we get a non-zero response.
    if result['json']['failed']:
        module.json_output['msg'] = 'The workflow "{0}" failed'.format(name)
        module.fail_json(**module.json_output)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
