#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2018, Sean O'Keeffe <seanokeeffe797@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: katello_content_view_version
short_description: Create, remove or interact with a Katello Content View Version
description:
  - Publish, Promote or Remove a Katello Content View Version
author: Sean O'Keeffe (@sean797)
notes:
  - You cannot use this to remove a Content View Version from a Lifecycle environment, you should promote another version first.
  - For idempotency you must specify either C(version) or C(current_lifecycle_environment).
options:
  content_view:
    description:
      - Name of the content view
    required: true
    type: str
  description:
    description:
      - Description of the Content View Version
    type: str
  organization:
    description:
      - Organization that the content view is in
    required: true
    type: str
  state:
    description:
      - Content View Version state
    default: present
    choices:
      - absent
      - present
    type: str
  version:
    description:
      - The content view version number (i.e. 1.0)
    type: str
  lifecycle_environments:
    description:
      - The lifecycle environments the Content View Version should be in.
    type: list
  force_promote:
    description:
      - Force content view promotion and bypass lifecycle environment restriction
    default: false
    type: bool
    aliases:
      - force
  force_yum_metadata_regeneration:
    description:
      - Force metadata regeneration when performing Publish and Promote tasks
    type: bool
    default: false
  synchronous:
    description:
      - Wait for the Publish or Promote task to complete if True. Immediately return if False.
    default: true
    type: bool
  current_lifecycle_environment:
    description:
      - The lifecycle environment that is already associated with the content view version
      - Helpful for promoting a content view version
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Ensure content view version 2.0 is in Test & Pre Prod"
  katello_content_view_version:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    content_view: "CV 1"
    organization: "Default Organization"
    version: 2.0
    lifecycle_environments:
      - Test
      - Pre Prod

- name: "Ensure content view version in Test is also in Pre Prod"
  katello_content_view_version:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    content_view: "CV 1"
    organization: "Default Organization"
    current_lifecycle_environment: Test
    lifecycle_environments:
      - Pre Prod

- name: "Publish a content view, not idempotent"
  katello_content_view_version:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    content_view: "CV 1"
    organization: "Default Organization"

- name: "Publish a content view and promote that version to Library & Dev, not idempotent"
  katello_content_view_version:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    content_view: "CV 1"
    organization: "Default Organization"
    lifecycle_environments:
      - Library
      - Dev

- name: "Ensure content view version 1.0 doesn't exist"
  katello_content_view_version:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    content_view: "Web Servers"
    organization: "Default Organization"
    version: 1.0
    state: absent
'''

RETURN = ''' # '''


from ansible.module_utils.foreman_helper import KatelloEntityAnsibleModule


def promote_content_view_version(module, content_view_version, environments, synchronous, force, force_yum_metadata_regeneration):
    changed = False

    current_environment_ids = {environment['id'] for environment in content_view_version['environments']}
    desired_environment_ids = {environment['id'] for environment in environments}
    promote_to_environment_ids = list(desired_environment_ids - current_environment_ids)

    if promote_to_environment_ids:
        payload = {
            'id': content_view_version['id'],
            'environment_ids': promote_to_environment_ids,
            'force': force,
            'force_yum_metadata_regeneration': force_yum_metadata_regeneration,
        }

        changed, _dummy = module.resource_action('content_view_versions', 'promote', params=payload, synchronous=synchronous)
    return changed


def main():
    module = KatelloEntityAnsibleModule(
        entity_spec=dict(
            content_view=dict(type='entity', flat_name='content_view_id', required=True),
            description=dict(),
            version=dict(),
            lifecycle_environments=dict(type='list'),
            force_promote=dict(type='bool', aliases=['force'], default=False),
            force_yum_metadata_regeneration=dict(type='bool', default=False),
            synchronous=dict(type='bool', default=True),
            current_lifecycle_environment=dict(),
        ),
        mutually_exclusive=[['current_lifecycle_environment', 'version']],
    )

    module.task_timeout = 60 * 60

    entity_dict = module.clean_params()

    # Do an early (not exhaustive) sanity check, whether we can perform this non-synchronous
    if (
        not module.desired_absent and 'lifecycle_environments' in entity_dict
        and 'version' not in entity_dict and 'current_lifecycle_environment' not in entity_dict
        and not entity_dict['synchronous']
    ):
        module.fail_json(msg="Cannot perform non-blocking publishing and promoting in the same module call.")

    module.connect()

    entity_dict['organization'] = module.find_resource_by_name('organizations', entity_dict['organization'], thin=True)
    scope = {'organization_id': entity_dict['organization']['id']}

    content_view = module.find_resource_by_name('content_views', name=entity_dict['content_view'], params=scope)

    if 'current_lifecycle_environment' in entity_dict:
        entity_dict['current_lifecycle_environment'] = module.find_resource_by_name(
            'lifecycle_environments', name=entity_dict['current_lifecycle_environment'], params=scope)
        search_scope = {'content_view_id': content_view['id'], 'environment_id': entity_dict['current_lifecycle_environment']['id']}
        content_view_version = module.find_resource('content_view_versions', search=None, params=search_scope)
    elif 'version' in entity_dict:
        search = "content_view_id={0},version={1}".format(content_view['id'], entity_dict['version'])
        content_view_version = module.find_resource('content_view_versions', search=search, failsafe=True)
    else:
        content_view_version = None

    changed = False
    le_changed = False
    if module.desired_absent:
        changed = module.ensure_entity_state('content_view_versions', None, content_view_version, params=scope)
    else:
        if content_view_version is None:
            # Do a sanity check, whether we can perform this non-synchronous
            if 'lifecycle_environments' in entity_dict and not entity_dict['synchronous']:
                module.fail_json(msg="Cannot perform non-blocking publishing and promoting in the same module call.")

            payload = {
                'id': content_view['id'],
            }
            if 'description' in entity_dict:
                payload['description'] = entity_dict['description']
            if 'force_yum_metadata_regeneration' in entity_dict:
                payload['force_yum_metadata_regeneration'] = entity_dict['force_yum_metadata_regeneration']
            if 'version' in entity_dict:
                split_version = list(map(int, str(entity_dict['version']).split('.')))
                payload['major'] = split_version[0]
                payload['minor'] = split_version[1]

            changed, response = module.resource_action('content_views', 'publish', params=payload, synchronous=entity_dict['synchronous'])
            # workaround for https://projects.theforeman.org/issues/28138
            content_view_version_id = response['output'].get('content_view_version_id') or response['input'].get('content_view_version_id')
            content_view_version = module.show_resource('content_view_versions', content_view_version_id)

        if 'lifecycle_environments' in entity_dict:
            lifecycle_environments = module.find_resources_by_name('lifecycle_environments', names=entity_dict['lifecycle_environments'], params=scope)
            le_changed = promote_content_view_version(
                module, content_view_version, lifecycle_environments, synchronous=entity_dict['synchronous'],
                force=entity_dict['force_promote'],
                force_yum_metadata_regeneration=entity_dict['force_yum_metadata_regeneration'],
            )

    module.exit_json(changed=changed or le_changed)


if __name__ == '__main__':
    main()
