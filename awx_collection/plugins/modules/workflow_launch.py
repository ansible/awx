#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: workflow_launch
author: "John Westcott IV (@john-westcott-iv)"
short_description: Run a workflow in Automation Platform Controller
description:
    - Launch an Automation Platform Controller workflows. See
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
- name: Launch a workflow with a timeout of 10 seconds
  workflow_launch:
    workflow_template: "Test Workflow"
    timeout: 10

- name: Launch a Workflow with extra_vars without waiting
  workflow_launch:
    workflow_template: "Test workflow"
    extra_vars:
      var1: My First Variable
      var2: My Second Variable
    wait: False
'''

from ..module_utils.controller_api import ControllerAPIModule
import json


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
        interval=dict(required=False, default=2.0, type='float'),
        timeout=dict(required=False, type='int'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

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
    for arg_name, arg_value in optional_args.items():
        if arg_value:
            post_data[arg_name] = arg_value

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    if inventory:
        post_data['inventory'] = module.resolve_name_to_id('inventories', inventory)

    # Attempt to look up job_template based on the provided name
    lookup_data = {}
    if organization:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    workflow_job_template = module.get_one('workflow_job_templates', name_or_id=name, data=lookup_data)

    if workflow_job_template is None:
        module.fail_json(msg="Unable to find workflow job template")

    # The API will allow you to submit values to a jb launch that are not prompt on launch.
    # Therefore, we will test to see if anything is set which is not prompt on launch and fail.
    check_vars_to_prompts = {
        'inventory': 'ask_inventory_on_launch',
        'limit': 'ask_limit_on_launch',
        'scm_branch': 'ask_scm_branch_on_launch',
    }

    param_errors = []
    for variable_name, prompt in check_vars_to_prompts.items():
        if variable_name in post_data and not workflow_job_template[prompt]:
            param_errors.append("The field {0} was specified but the workflow job template does not allow for it to be overridden".format(variable_name))
    # Check if Either ask_variables_on_launch, or survey_enabled is enabled for use of extra vars.
    if module.params.get('extra_vars') and not (workflow_job_template['ask_variables_on_launch'] or workflow_job_template['survey_enabled']):
        param_errors.append("The field extra_vars was specified but the workflow job template does not allow for it to be overridden")
    if len(param_errors) > 0:
        module.fail_json(msg="Parameters specified which can not be passed into workflow job template, see errors for details", errors=param_errors)

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

    # Invoke wait function
    module.wait_on_url(url=result['json']['url'], object_name=name, object_type='Workflow Job', timeout=timeout, interval=interval)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
