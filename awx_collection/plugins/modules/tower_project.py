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
module: tower_project
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Ansible Tower projects
description:
    - Create, update, or destroy Ansible Tower projects. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the project.
      required: True
      type: str
    description:
      description:
        - Description to use for the project.
      type: str
    scm_type:
      description:
        - Type of SCM resource.
      choices: ["manual", "git", "hg", "svn", "insights"]
      default: "manual"
      type: str
    scm_url:
      description:
        - URL of SCM resource.
      type: str
    local_path:
      description:
        - The server playbook directory for manual projects.
      type: str
    scm_branch:
      description:
        - The branch to use for the SCM resource.
      type: str
      default: ''
    scm_refspec:
      description:
        - The refspec to use for the SCM resource.
      type: str
      default: ''
    credential:
      description:
        - Name of the credential to use with this SCM resource.
      type: str
      aliases:
        - scm_credential
    scm_clean:
      description:
        - Remove local modifications before updating.
      type: bool
      default: 'no'
    scm_delete_on_update:
      description:
        - Remove the repository completely before updating.
      type: bool
      default: 'no'
    scm_update_on_launch:
      description:
        - Before an update to the local repository before launching a job with this project.
      type: bool
      default: 'no'
    scm_update_cache_timeout:
      description:
        - Cache Timeout to cache prior project syncs for a certain number of seconds.
            Only valid if scm_update_on_launch is to True, otherwise ignored.
      type: int
      default: 0
    allow_override:
      description:
        - Allow changing the SCM branch or revision in a job template that uses this project.
      type: bool
      aliases:
        - scm_allow_override
    timeout:
      description:
        - The amount of time (in seconds) to run before the SCM Update is canceled. A value of 0 means no timeout.
      default: 0
      type: int
      aliases:
        - job_timeout
    custom_virtualenv:
      description:
        - Local absolute file path containing a custom Python virtualenv to use
      type: str
      default: ''
    organization:
      description:
        - Name of organization for project.
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    wait:
      description:
        - Provides option (True by default) to wait for completed project sync
          before returning
        - Can assure playbook files are populated so that job templates that rely
          on the project may be successfully created
      type: bool
      default: True
    notification_templates_started:
      description:
        - list of notifications to send on start
      type: list
      elements: str
    notification_templates_success:
      description:
        - list of notifications to send on success
      type: list
      elements: str
    notification_templates_error:
      description:
        - list of notifications to send on error
      type: list
      elements: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add tower project
  tower_project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add Tower Project with cache timeout and custom virtualenv
  tower_project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    scm_update_on_launch: True
    scm_update_cache_timeout: 60
    custom_virtualenv: "/var/lib/awx/venv/ansible-2.2"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

import time

from ..module_utils.tower_api import TowerAPIModule


def wait_for_project_update(module, last_request):
    # The current running job for the udpate is in last_request['summary_fields']['current_update']['id']

    if 'current_update' in last_request['summary_fields']:
        running = True
        while running:
            result = module.get_endpoint('/project_updates/{0}/'.format(last_request['summary_fields']['current_update']['id']))['json']

            if module.is_job_done(result['status']):
                time.sleep(1)
                running = False

        if result['status'] != 'successful':
            module.fail_json(msg="Project update failed")

    module.exit_json(**module.json_output)


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        scm_type=dict(choices=['manual', 'git', 'hg', 'svn', 'insights'], default='manual'),
        scm_url=dict(),
        local_path=dict(),
        scm_branch=dict(default=''),
        scm_refspec=dict(default=''),
        credential=dict(aliases=['scm_credential']),
        scm_clean=dict(type='bool', default=False),
        scm_delete_on_update=dict(type='bool', default=False),
        scm_update_on_launch=dict(type='bool', default=False),
        scm_update_cache_timeout=dict(type='int', default=0),
        allow_override=dict(type='bool', aliases=['scm_allow_override']),
        timeout=dict(type='int', default=0, aliases=['job_timeout']),
        custom_virtualenv=dict(),
        organization=dict(),
        notification_templates_started=dict(type="list", elements='str'),
        notification_templates_success=dict(type="list", elements='str'),
        notification_templates_error=dict(type="list", elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
        wait=dict(type='bool', default=True),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    description = module.params.get('description')
    scm_type = module.params.get('scm_type')
    if scm_type == "manual":
        scm_type = ""
    scm_url = module.params.get('scm_url')
    local_path = module.params.get('local_path')
    scm_branch = module.params.get('scm_branch')
    scm_refspec = module.params.get('scm_refspec')
    credential = module.params.get('credential')
    scm_clean = module.params.get('scm_clean')
    scm_delete_on_update = module.params.get('scm_delete_on_update')
    scm_update_on_launch = module.params.get('scm_update_on_launch')
    scm_update_cache_timeout = module.params.get('scm_update_cache_timeout')
    allow_override = module.params.get('allow_override')
    timeout = module.params.get('timeout')
    custom_virtualenv = module.params.get('custom_virtualenv')
    organization = module.params.get('organization')
    state = module.params.get('state')
    wait = module.params.get('wait')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    lookup_data = {}
    org_id = None
    if organization:
        org_id = module.resolve_name_to_id('organizations', organization)
        lookup_data['organization'] = org_id

    # Attempt to look up project based on the provided name and org ID
    project = module.get_one('projects', name_or_id=name, data=lookup_data)

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(project)

    if credential is not None:
        credential = module.resolve_name_to_id('credentials', credential)

    # Attempt to look up associated field items the user specified.
    association_fields = {}

    notifications_start = module.params.get('notification_templates_started')
    if notifications_start is not None:
        association_fields['notification_templates_started'] = []
        for item in notifications_start:
            association_fields['notification_templates_started'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_success = module.params.get('notification_templates_success')
    if notifications_success is not None:
        association_fields['notification_templates_success'] = []
        for item in notifications_success:
            association_fields['notification_templates_success'].append(module.resolve_name_to_id('notification_templates', item))

    notifications_error = module.params.get('notification_templates_error')
    if notifications_error is not None:
        association_fields['notification_templates_error'] = []
        for item in notifications_error:
            association_fields['notification_templates_error'].append(module.resolve_name_to_id('notification_templates', item))

    # Create the data that gets sent for create and update
    project_fields = {
        'name': module.get_item_name(project) if project else name,
        'scm_type': scm_type,
        'scm_url': scm_url,
        'scm_branch': scm_branch,
        'scm_refspec': scm_refspec,
        'scm_clean': scm_clean,
        'scm_delete_on_update': scm_delete_on_update,
        'timeout': timeout,
        'organization': org_id,
        'scm_update_on_launch': scm_update_on_launch,
        'scm_update_cache_timeout': scm_update_cache_timeout,
        'custom_virtualenv': custom_virtualenv,
    }
    if description is not None:
        project_fields['description'] = description
    if credential is not None:
        project_fields['credential'] = credential
    if allow_override is not None:
        project_fields['allow_override'] = allow_override
    if scm_type == '':
        project_fields['local_path'] = local_path

    if scm_update_cache_timeout != 0 and scm_update_on_launch is not True:
        module.warn('scm_update_cache_timeout will be ignored since scm_update_on_launch was not set to true')

    # If we are doing a not manual project, register our on_change method
    # An on_change function, if registered, will fire after an post_endpoint or update_if_needed completes successfully
    on_change = None
    if wait and scm_type != '':
        on_change = wait_for_project_update

    # If the state was present and we can let the module build or update the existing project, this will return on its own
    module.create_or_update_if_needed(
        project, project_fields,
        endpoint='projects', item_type='project',
        associations=association_fields,
        on_create=on_change, on_update=on_change
    )


if __name__ == '__main__':
    main()
