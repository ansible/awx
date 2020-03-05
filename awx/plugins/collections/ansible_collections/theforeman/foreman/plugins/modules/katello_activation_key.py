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
module: katello_activation_key
short_description: Create and Manage Katello activation keys
description:
  - Create and Manage Katello activation keys
author: "Andrew Kofink (@akofink)"
options:
  name:
    description:
      - Name of the activation key
    required: true
    type: str
  organization:
    description:
      - Organization name that the activation key is in
    required: true
    type: str
  lifecycle_environment:
    description:
      - Name of the lifecycle environment
    type: str
  content_view:
    description:
      - Name of the content view
    type: str
  subscriptions:
    description:
      - List of subscriptions that include either Name or Pool ID.
      - Pool IDs are preferred since Names are not unique and the module will fail if it finds more than one subscription with the same name.
    type: list
    suboptions:
      name:
        description:
          - Name of the Subscription to be added.
          - Mutually exclusive with I(pool_id).
        type: str
        required: false
      pool_id:
        description:
          - Pool ID of the Subscription to be added.
          - Mutually exclusive with I(name).
        type: str
        required: false
  host_collections:
    description:
      - List of host collections to add to activation key
    type: list
  content_overrides:
    description:
      - List of content overrides that include label and override state ('enabled', 'disabled' or 'default')
    type: list
    suboptions:
      label:
        description:
          - Label of the content override
        type: str
        required: true
      override:
        description:
          - Override value
        choices:
          - enabled
          - disabled
        type: str
        required: true
  auto_attach:
    description:
      - Set Auto-Attach on or off
    type: bool
  release_version:
    description:
      - Set the content release version
    type: str
  service_level:
    description:
      - Set the service level
    choices:
      - Self-Support
      - Standard
      - Premium
    type: str
  state:
    description:
      - State of the Activation Key
      - If C(copied) the key will be copied to a new one with I(new_name) as the name and all other fields left untouched
      - C(present_with_defaults) will ensure the entity exists, but won't update existing ones
    default: present
    choices:
      - present
      - present_with_defaults
      - absent
      - copied
    type: str
  new_name:
    description:
      - Name of the new activation key when state == copied
    type: str
extends_documentation_fragment: foreman
'''

EXAMPLES = '''
- name: "Create katello client activation key"
  katello_activation_key:
    username: "admin"
    password: "changeme"
    server_url: "https://foreman.example.com"
    name: "Katello Clients"
    organization: "Default Organization"
    lifecycle_environment: "Library"
    content_view: 'client content view'
    host_collections:
        - rhel7-servers
        - rhel7-production
    subscriptions:
      - pool_id: "8a88e9826db22df5016dd018abdd029b"
      - pool_id: "8a88e9826db22df5016dd01a23270344"
      - name: "Red Hat Enterprise Linux"
    content_overrides:
        - label: rhel-7-server-optional-rpms
          override: enabled
    auto_attach: False
    release_version: 7Server
    service_level: Standard
'''

RETURN = ''' # '''

from ansible.module_utils.foreman_helper import KatelloEntityAnsibleModule


def override_to_boolnone(override):
    value = None
    if isinstance(override, bool):
        value = override
    else:
        override = override.lower()
        if override == 'enabled':
            value = True
        elif override == 'disabled':
            value = False
        elif override == 'default':
            value = None
    return value


def main():
    module = KatelloEntityAnsibleModule(
        entity_spec=dict(
            name=dict(required=True),
            new_name=dict(),
            lifecycle_environment=dict(type='entity', flat_name='environment_id'),
            content_view=dict(type='entity', flat_name='content_view_id'),
            host_collections=dict(type='entity_list', flat_name='host_collection_ids'),
            auto_attach=dict(type='bool'),
            release_version=dict(),
            service_level=dict(choices=['Self-Support', 'Standard', 'Premium']),
        ),
        argument_spec=dict(
            subscriptions=dict(type='list', elements='dict', options=dict(
                name=dict(),
                pool_id=dict(),
            ),
                required_one_of=[['name', 'pool_id']],
                mutually_exclusive=[['name', 'pool_id']],
            ),
            content_overrides=dict(type='list', elements='dict', options=dict(
                label=dict(required=True),
                override=dict(required=True, choices=['enabled', 'disabled']),
            )),
            state=dict(default='present', choices=['present', 'present_with_defaults', 'absent', 'copied']),
        ),
        required_if=[
            ['state', 'copied', ['new_name']],
        ],
    )

    entity_dict = module.clean_params()

    module.connect()

    entity_dict['organization'] = module.find_resource_by_name('organizations', entity_dict['organization'], thin=True)
    scope = {'organization_id': entity_dict['organization']['id']}
    if not module.desired_absent:
        if 'lifecycle_environment' in entity_dict:
            entity_dict['lifecycle_environment'] = module.find_resource_by_name(
                'lifecycle_environments', entity_dict['lifecycle_environment'], params=scope, thin=True)

        if 'content_view' in entity_dict:
            entity_dict['content_view'] = module.find_resource_by_name('content_views', entity_dict['content_view'], params=scope, thin=True)

    entity = module.find_resource_by_name('activation_keys', name=entity_dict['name'], params=scope, failsafe=True)

    if module.state == 'copied':
        new_entity = module.find_resource_by_name('activation_keys', name=entity_dict['new_name'], params=scope, failsafe=True)
        if new_entity is not None:
            module.warn("Activation Key '{0}' already exists.".format(entity_dict['new_name']))
            module.exit_json(changed=False)

    subscriptions = entity_dict.pop('subscriptions', None)
    content_overrides = entity_dict.pop('content_overrides', None)
    host_collections = entity_dict.pop('host_collections', None)
    changed, activation_key = module.ensure_entity('activation_keys', entity_dict, entity, params=scope)

    # only update subscriptions of newly created or updated AKs
    # copied keys inherit the subscriptions of the origin, so one would not have to specify them again
    # deleted keys don't need subscriptions anymore either
    if module.state == 'present' or (module.state == 'present_with_defaults' and changed):
        # the auto_attach, release_version and service_level parameters can only be set on an existing AK with an update,
        # not during create, so let's force an update. see https://projects.theforeman.org/issues/27632 for details
        if any(key in entity_dict for key in ['auto_attach', 'release_version', 'service_level']) and changed:
            _activation_key_changed, activation_key = module.ensure_entity('activation_keys', entity_dict, activation_key, params=scope)

        ak_scope = {'activation_key_id': activation_key['id']}
        if subscriptions is not None:
            desired_subscriptions = []
            for subscription in subscriptions:
                if subscription['name'] is not None and subscription['pool_id'] is None:
                    desired_subscriptions.append(module.find_resource_by_name('subscriptions', subscription['name'], params=scope, thin=True))
                if subscription['pool_id'] is not None:
                    desired_subscriptions.append(module.find_resource_by_id('subscriptions', subscription['pool_id'], params=scope, thin=True))
            desired_subscription_ids = set(item['id'] for item in desired_subscriptions)
            current_subscriptions = module.list_resource('subscriptions', params=ak_scope)
            current_subscription_ids = set(item['id'] for item in current_subscriptions)

            if desired_subscription_ids != current_subscription_ids:
                module.record_before('activation_keys/subscriptions', {'id': activation_key['id'], 'subscriptions': current_subscription_ids})
                module.record_after('activation_keys/subscriptions', {'id': activation_key['id'], 'subscriptions': desired_subscription_ids})
                module.record_after_full('activation_keys/subscriptions', {'id': activation_key['id'], 'subscriptions': desired_subscription_ids})

                ids_to_remove = current_subscription_ids - desired_subscription_ids
                if ids_to_remove:
                    payload = {
                        'id': activation_key['id'],
                        'subscriptions': [{'id': item} for item in ids_to_remove],
                    }
                    payload.update(scope)
                    module.resource_action('activation_keys', 'remove_subscriptions', payload)

                ids_to_add = desired_subscription_ids - current_subscription_ids
                if ids_to_add:
                    payload = {
                        'id': activation_key['id'],
                        'subscriptions': [{'id': item, 'quantity': 1} for item in ids_to_add],
                    }
                    payload.update(scope)
                    module.resource_action('activation_keys', 'add_subscriptions', payload)

                changed = True

        if content_overrides is not None:
            _product_content_changed, product_content = module.resource_action('activation_keys', 'product_content',
                                                                               params={'id': activation_key['id']}, ignore_check_mode=True)
            current_content_overrides = {
                product['content']['label']: product['enabled_content_override']
                for product in product_content['results']
                if product['enabled_content_override'] is not None
            }
            desired_content_overrides = {
                product['label']: override_to_boolnone(product['override']) for product in content_overrides
            }
            changed_content_overrides = []

            module.record_before('activation_keys/content_overrides', {'id': activation_key['id'], 'content_overrides': current_content_overrides.copy()})
            module.record_after('activation_keys/content_overrides', {'id': activation_key['id'], 'content_overrides': desired_content_overrides})
            module.record_after_full('activation_keys/content_overrides', {'id': activation_key['id'], 'content_overrides': desired_content_overrides})

            for label, override in desired_content_overrides.items():
                if override != current_content_overrides.pop(label, None):
                    changed_content_overrides.append({'content_label': label, 'value': override})
            for label in current_content_overrides.keys():
                changed_content_overrides.append({'content_label': label, 'reset': True})

            if changed_content_overrides:
                payload = {
                    'id': activation_key['id'],
                    'content_overrides': changed_content_overrides,
                }
                module.resource_action('activation_keys', 'content_override', payload)
                changed = True

        if host_collections is not None:
            if 'host_collection_ids' in activation_key:
                current_host_collection_ids = set(activation_key['host_collection_ids'])
            else:
                current_host_collection_ids = set(item['id'] for item in activation_key['host_collections'])
            desired_host_collections = module.find_resources_by_name('host_collections', host_collections, params=scope, thin=True)
            desired_host_collection_ids = set(item['id'] for item in desired_host_collections)

            if desired_host_collection_ids != current_host_collection_ids:
                module.record_before('activation_keys/host_collections', {'id': activation_key['id'], 'host_collections': current_host_collection_ids})
                module.record_after('activation_keys/host_collections', {'id': activation_key['id'], 'host_collections': desired_host_collection_ids})
                module.record_after_full('activation_keys/host_collections', {'id': activation_key['id'], 'host_collections': desired_host_collection_ids})

                ids_to_remove = current_host_collection_ids - desired_host_collection_ids
                if ids_to_remove:
                    payload = {
                        'id': activation_key['id'],
                        'host_collection_ids': list(ids_to_remove),
                    }
                    module.resource_action('activation_keys', 'remove_host_collections', payload)

                ids_to_add = desired_host_collection_ids - current_host_collection_ids
                if ids_to_add:
                    payload = {
                        'id': activation_key['id'],
                        'host_collection_ids': list(ids_to_add),
                    }
                    module.resource_action('activation_keys', 'add_host_collections', payload)

                changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
