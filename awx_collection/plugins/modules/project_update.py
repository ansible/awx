#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: project_update
author: "Sean Sullivan (@sean-m-sullivan)"
short_description: Update a Project in Automation Platform Controller
description:
    - Update a Automation Platform Controller Project. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name or id of the project to update.
      required: True
      type: str
      aliases:
        - project
    organization:
      description:
        - Organization the project exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
    wait:
      description:
        - Wait for the project to update.
        - If scm revision has not changed module will return not changed.
      default: True
      type: bool
    interval:
      description:
        - The interval to request an update from the controller.
      required: False
      default: 1
      type: float
    timeout:
      description:
        - If waiting for the project to update this will abort after this
          amount of seconds
      type: int
extends_documentation_fragment: awx.awx.auth
'''

RETURN = '''
id:
    description: project id of the updated project
    returned: success
    type: int
    sample: 86
status:
    description: status of the updated project
    returned: success
    type: str
    sample: pending
'''


EXAMPLES = '''
- name: Launch a project with a timeout of 10 seconds
  project_update:
    project: "Networking Project"
    timeout: 10

- name: Launch a Project with extra_vars without waiting
  project_update:
    project: "Networking Project"
    wait: False
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True, aliases=['project']),
        organization=dict(),
        wait=dict(default=True, type='bool'),
        interval=dict(default=1.0, type='float'),
        timeout=dict(default=None, type='int'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    organization = module.params.get('organization')
    wait = module.params.get('wait')
    interval = module.params.get('interval')
    timeout = module.params.get('timeout')

    # Attempt to look up project based on the provided name or id
    lookup_data = {}
    if organization:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', organization)
    project = module.get_one('projects', name_or_id=name, data=lookup_data)
    if project is None:
        module.fail_json(msg="Unable to find project")

    if wait:
        scm_revision_original = project['scm_revision']

    # Update the project
    result = module.post_endpoint(project['related']['update'])

    if result['status_code'] != 202:
        module.fail_json(msg="Failed to update project, see response for details", response=result)

    module.json_output['changed'] = True
    module.json_output['id'] = result['json']['id']
    module.json_output['status'] = result['json']['status']

    if not wait:
        module.exit_json(**module.json_output)

    # Invoke wait function
    result = module.wait_on_url(
        url=result['json']['url'], object_name=module.get_item_name(project), object_type='Project Update', timeout=timeout, interval=interval
    )
    scm_revision_new = result['json']['scm_revision']
    if scm_revision_new == scm_revision_original:
        module.json_output['changed'] = False

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
