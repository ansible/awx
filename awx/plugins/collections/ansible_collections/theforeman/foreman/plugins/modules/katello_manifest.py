#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Andrew Kofink <ajkofink@gmail.com>
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
module: katello_manifest
short_description: Manage Katello manifests
description:
    - Upload and Manage Katello manifests
author: "Andrew Kofink (@akofink)"
options:
  organization:
    description:
      - Organization that the manifest is in
    required: true
    type: str
  manifest_path:
    description:
      - Path to the manifest zip file
      - This parameter will be ignored if I(state=absent) or I(state=refreshed)
    type: path
  state:
    description:
      - The state of the manifest
    default: present
    choices:
      - absent
      - present
      - refreshed
    type: str
  repository_url:
    description:
       - URL to retrieve content from
    aliases: [ redhat_repository_url ]
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Upload the RHEL developer edition manifest"
  katello_manifest:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    organization: "Default Organization"
    state: present
    manifest_path: "/tmp/manifest.zip"
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import KatelloEntityAnsibleModule


def main():
    module = KatelloEntityAnsibleModule(
        argument_spec=dict(
            manifest_path=dict(type='path'),
            state=dict(default='present', choices=['absent', 'present', 'refreshed']),
            repository_url=dict(aliases=['redhat_repository_url']),
        ),
        required_if=[
            ['state', 'present', ['manifest_path']],
        ],
    )

    module.task_timeout = 5 * 60

    entity_dict = module.clean_params()

    module.connect()

    organization = module.find_resource_by_name('organizations', name=entity_dict['organization'], thin=False)
    scope = {'organization_id': organization['id']}

    try:
        existing_manifest = organization['owner_details']['upstreamConsumer']
    except KeyError:
        existing_manifest = None

    changed = False
    if module.state == 'present':
        if 'repository_url' in entity_dict:
            payload = {'redhat_repository_url': entity_dict['repository_url']}
            org_spec = dict(redhat_repository_url=dict())
            changed_url, organization = module.ensure_entity('organizations', payload, organization, state='present', entity_spec=org_spec)
        else:
            changed_url = False

        try:
            with open(entity_dict['manifest_path'], 'rb') as manifest_file:
                files = {'content': (entity_dict['manifest_path'], manifest_file, 'application/zip')}
                params = {}
                if 'repository_url' in entity_dict:
                    params['repository_url'] = entity_dict['repository_url']
                params.update(scope)
                changed, result = module.resource_action('subscriptions', 'upload', params, files=files)
                for error in result['humanized']['errors']:
                    if "same as existing data" in error:
                        changed = False
                    elif "older than existing data" in error:
                        module.fail_json(msg="Manifest is older than existing data.")
                    else:
                        module.fail_json(msg="Upload of the manifest failed: %s" % error)
                changed |= changed_url
        except IOError as e:
            module.fail_json(msg="Unable to read the manifest file: %s" % e)
    elif module.desired_absent and existing_manifest:
        changed, result = module.resource_action('subscriptions', 'delete_manifest', scope)
    elif module.state == 'refreshed':
        if existing_manifest:
            changed, result = module.resource_action('subscriptions', 'refresh_manifest', scope)
        else:
            module.fail_json(msg="No manifest found to refresh.")

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
