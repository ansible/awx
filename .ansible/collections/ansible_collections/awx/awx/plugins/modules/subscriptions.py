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
options:
    username:
      description:
        - Red Hat or Red Hat Satellite username to get available subscriptions.
        - The credentials you use will be stored for future use in retrieving renewal or expanded subscriptions
      required: True
      type: str
    password:
      description:
        - Red Hat or Red Hat Satellite password to get available subscriptions.
        - The credentials you use will be stored for future use in retrieving renewal or expanded subscriptions
      required: True
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
    username: "my_username"
    password: "My Password"

- name: Get subscriptions with a filter
  subscriptions:
    username: "my_username"
    password: "My Password"
    filters:
      product_name: "Red Hat Ansible Automation Platform"
      support_level: "Self-Support"
'''

from ..module_utils.controller_api import ControllerAPIModule


def main():

    module = ControllerAPIModule(
        argument_spec=dict(
            username=dict(type='str', required=True),
            password=dict(type='str', no_log=True, required=True),
            filters=dict(type='dict', required=False, default={}),
        ),
    )

    json_output = {'changed': False}

    # Check if Tower is already licensed
    post_data = {
        'subscriptions_password': module.params.get('password'),
        'subscriptions_username': module.params.get('username'),
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
