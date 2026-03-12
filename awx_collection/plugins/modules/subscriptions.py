#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2019, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: subscriptions
author: "John Westcott IV (@john-westcott-iv)"
short_description: Get subscription list
description:
    - Get subscriptions available to Automation Platform Controller. See
      U(https://www.ansible.com/tower) for an overview.
    - The credentials you use will be stored for future use in retrieving renewal or expanded subscriptions
options:
    username:
      description:
        - Red Hat username to get available subscriptions.
      required: False
      type: str
    password:
      description:
        - Red Hat password to get available subscriptions.
      required: False
      type: str
    client_id:
      description:
        - Red Hat service account client ID to get available subscriptions.
      required: False
      type: str
    client_secret:
      description:
        - Red Hat service account client secret to get available subscriptions.
      required: False
      type: str
    filters:
      description:
        - Client side filters to apply to the subscriptions.
        - For any entries in this dict, if there is a corresponding entry in the subscription it must contain the value from this dict
        - Note This is a client side search, not an API side search
      required: False
      type: dict
      default: {}
extends_documentation_fragment: awx.awx.auth
'''

RETURN = '''
subscriptions:
    description: dictionary containing information about the subscriptions
    returned: If login succeeded
    type: dict
'''

EXAMPLES = '''
- name: Get subscriptions
  subscriptions:
    client_id: "c6bd7594-d776-46e5-8156-6d17af147479"
    client_secret: "MO9QUvoOZ5fc5JQKXoTch1AsTLI7nFsZ"

- name: Get subscriptions with a filter
  subscriptions:
    client_id: "c6bd7594-d776-46e5-8156-6d17af147479"
    client_secret: "MO9QUvoOZ5fc5JQKXoTch1AsTLI7nFsZ"
    filters:
      product_name: "Red Hat Ansible Automation Platform"
      support_level: "Self-Support"
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():

    module = ControllerAPIModule(
        argument_spec=dict(
            username=dict(type='str', required=False),
            password=dict(type='str', no_log=True, required=False),
            client_id=dict(type='str', required=False),
            client_secret=dict(type='str', no_log=True, required=False),
            filters=dict(type='dict', required=False, default={}),
        ),
        mutually_exclusive=[
            ['username', 'client_id']
        ],
        required_together=[
            ['username', 'password'],
            ['client_id', 'client_secret']
        ],
        required_one_of=[
            ['username', 'client_id']
        ],
    )

    json_output = {'changed': False}
    username = module.params.get('username')
    password = module.params.get('password')
    client_id = module.params.get('client_id')
    client_secret = module.params.get('client_secret')

    if username and password:
        post_data = {
            'subscriptions_username': username,
            'subscriptions_password': password,
        }
    else:
        post_data = {
            'subscriptions_client_id': client_id,
            'subscriptions_client_secret': client_secret,
        }

    all_subscriptions = module.post_endpoint('config/subscriptions', data=post_data)['json']
    json_output['subscriptions'] = []
    for subscription in all_subscriptions:
        add = True
        for key in module.params.get('filters').keys():
            if subscription.get(key, None) and module.params.get('filters')[key] not in subscription.get(key):
                add = False
        if add:
            json_output['subscriptions'].append(subscription)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
