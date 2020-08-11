#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_project_update
author: "Sean Sullivan (@sean-m-sullivan)"
short_description: Sync a Project in Ansible Tower
description:
    - Sync an Ansible Tower Project. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name of the workflow template to run.
      required: True
      type: str
      aliases:
        - project
    organization:
      description:
        - Organization the workflow job template exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
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
    description: dictionary containing information about the project updated
    returned: If project synced
    type: dict
'''


EXAMPLES = '''
- name: Launch a workflow with a timeout of 10 seconds
  tower_project_update:
    project: "Networking Project"
    timeout: 10

- name: Launch a Workflow with extra_vars without waiting
  tower_project_update:
    project: "Networking Project"
    wait: False
'''

from ..module_utils.tower_api import TowerModule
import json
import time


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, aliases=['project']),
        organization=dict(),
        wait=dict(required=False, default=True, type='bool'),
        interval=dict(required=False, default=1.0, type='float'),
        timeout=dict(required=False, default=None, type='int'),
    )

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    organization = module.params.get('organization')
    wait = module.params.get('wait')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')

    # Attempt to look up project based on the provided name
    lookup_data = {'name': name}
    if organization:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    project = module.get_one('projects', data=lookup_data)

    if project is None:
        module.fail_json(msg="Unable to find workflow job template")

    # Launch the job
    result = module.post_endpoint(project['related']['update'])

    if result['status_code'] != 202:
        module.fail_json(msg="Failed to update project, see response for details", response=result)

    module.json_output['changed'] = True
    module.json_output['id'] = result['json']['id']
    module.json_output['status'] = result['json']['status']

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

    # If the update has failed, we want to raise a task failure for that so we get a non-zero response.
    if result['json']['failed']:
        module.json_output['msg'] = 'The project "{0}" failed'.format(name)
        module.fail_json(**module.json_output)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
