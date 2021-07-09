#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: project
author: "Wayne Witzel III (@wwitzel3)"
short_description: create, update, or destroy Automation Platform Controller projects
description:
    - Create, update, or destroy Automation Platform Controller projects. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the project.
      required: True
      type: str
    copy_from:
      description:
        - Name or id to copy the project from.
        - This will copy an existing project and change any parameters supplied.
        - The new project name will be the one provided in the name parameter.
        - The organization parameter is not used in this, to facilitate copy from one organization to another.
        - Provide the id or use the lookup plugin to provide the id if multiple projects share the same name.
      type: str
    description:
      description:
        - Description to use for the project.
      type: str
    scm_type:
      description:
        - Type of SCM resource.
      choices: ["manual", "git", "svn", "insights"]
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
    scm_track_submodules:
      description:
        - Track submodules latest commit on specified branch.
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
        - If waiting for the project to update this will abort after this
          amount of seconds
      default: 0
      type: int
      aliases:
        - job_timeout
    default_environment:
      description:
        - Default Execution Environment to use for jobs relating to the project.
      type: str
    custom_virtualenv:
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
        - Only compatible with older versions of AWX/Tower
        - Deprecated, will be removed in the future
      type: str
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
    update_project:
      description:
        - Force project to update after changes.
        - Used in conjunction with wait, interval, and timeout.
      default: False
      type: bool
    interval:
      description:
        - The interval to request an update from the controller.
        - Requires wait.
      required: False
      default: 1
      type: float
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add project
  project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add Project with cache timeout
  project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    scm_update_on_launch: True
    scm_update_cache_timeout: 60
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Copy project
  project:
    name: copy
    copy_from: test
    description: Foo copy project
    organization: Foo
    state: present
'''

import time

from ..module_utils.controller_api import ControllerAPIModule


def wait_for_project_update(module, last_request):
    # The current running job for the update is in last_request['summary_fields']['current_update']['id']

    # Get parameters that were not passed in
    update_project = module.params.get('update_project')
    wait = module.params.get('wait')
    timeout = module.params.get('timeout')
    interval = module.params.get('interval')
    scm_revision_original = last_request['scm_revision']

    if 'current_update' in last_request['summary_fields']:
        running = True
        while running:
            result = module.get_endpoint('/project_updates/{0}/'.format(last_request['summary_fields']['current_update']['id']))['json']

            if module.is_job_done(result['status']):
                time.sleep(1)
                running = False

        if result['status'] != 'successful':
            module.fail_json(msg="Project update failed")
    elif update_project:
        result = module.post_endpoint(last_request['related']['update'])

        if result['status_code'] != 202:
            module.fail_json(msg="Failed to update project, see response for details", response=result)

        if not wait:
            module.exit_json(**module.json_output)

        # Invoke wait function
        result_final = module.wait_on_url(
            url=result['json']['url'], object_name=module.get_item_name(last_request), object_type='Project Update', timeout=timeout, interval=interval
        )

        # Set Changed to correct value depending on if hash changed Also output refspec comparision
        module.json_output['changed'] = True
        if result_final['json']['scm_revision'] == scm_revision_original:
            module.json_output['changed'] = False

    module.exit_json(**module.json_output)


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        copy_from=dict(),
        description=dict(),
        scm_type=dict(choices=['manual', 'git', 'svn', 'insights'], default='manual'),
        scm_url=dict(),
        local_path=dict(),
        scm_branch=dict(),
        scm_refspec=dict(),
        credential=dict(aliases=['scm_credential']),
        scm_clean=dict(type='bool', default=False),
        scm_delete_on_update=dict(type='bool', default=False),
        scm_track_submodules=dict(type='bool', default=False),
        scm_update_on_launch=dict(type='bool', default=False),
        scm_update_cache_timeout=dict(type='int', default=0),
        allow_override=dict(type='bool', aliases=['scm_allow_override']),
        timeout=dict(type='int', default=0, aliases=['job_timeout']),
        default_environment=dict(),
        custom_virtualenv=dict(),
        organization=dict(),
        notification_templates_started=dict(type="list", elements='str'),
        notification_templates_success=dict(type="list", elements='str'),
        notification_templates_error=dict(type="list", elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
        wait=dict(type='bool', default=True),
        update_project=dict(default=False, type='bool'),
        interval=dict(default=1.0, type='float'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    copy_from = module.params.get('copy_from')
    scm_type = module.params.get('scm_type')
    if scm_type == "manual":
        scm_type = ""
    local_path = module.params.get('local_path')
    credential = module.params.get('credential')
    scm_update_on_launch = module.params.get('scm_update_on_launch')
    scm_update_cache_timeout = module.params.get('scm_update_cache_timeout')
    default_ee = module.params.get('default_environment')
    organization = module.params.get('organization')
    state = module.params.get('state')
    wait = module.params.get('wait')
    update_project = module.params.get('update_project')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    lookup_data = {}
    org_id = None
    if organization:
        org_id = module.resolve_name_to_id('organizations', organization)
        lookup_data['organization'] = org_id

    # Attempt to look up project based on the provided name and org ID
    project = module.get_one('projects', name_or_id=name, data=lookup_data)

    # Attempt to look up credential to copy based on the provided name
    if copy_from:
        # a new existing item is formed when copying and is returned.
        project = module.copy_item(
            project,
            copy_from,
            name,
            endpoint='projects',
            item_type='project',
            copy_lookup_data={},
        )

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
        'organization': org_id,
        'scm_update_on_launch': scm_update_on_launch,
        'scm_update_cache_timeout': scm_update_cache_timeout,
    }

    for field_name in (
        'scm_url',
        'scm_branch',
        'scm_refspec',
        'scm_clean',
        'scm_delete_on_update',
        "scm_track_submodules",
        'timeout',
        'scm_update_cache_timeout',
        'custom_virtualenv',
        'description',
        'allow_override',
    ):
        field_val = module.params.get(field_name)
        if field_val is not None:
            project_fields[field_name] = field_val

    if credential is not None:
        project_fields['credential'] = credential
    if default_ee is not None:
        project_fields['default_environment'] = module.resolve_name_to_id('execution_environments', default_ee)
    if scm_type == '':
        if local_path is not None:
            project_fields['local_path'] = local_path

    if scm_update_cache_timeout != 0 and scm_update_on_launch is not True:
        module.warn('scm_update_cache_timeout will be ignored since scm_update_on_launch was not set to true')

    # If we are doing a not manual project, register our on_change method
    # An on_change function, if registered, will fire after an post_endpoint or update_if_needed completes successfully
    on_change = None
    if wait and scm_type != '' or update_project and scm_type != '':
        on_change = wait_for_project_update

    # If the state was present and we can let the module build or update the existing project, this will return on its own
    response = module.create_or_update_if_needed(
        project,
        project_fields,
        endpoint='projects',
        item_type='project',
        associations=association_fields,
        on_create=on_change,
        on_update=on_change,
        auto_exit=not update_project,
    )

    if update_project:
        wait_for_project_update(module, response)
    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
