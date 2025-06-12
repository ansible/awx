#!/usr/bin/python

# Same licensing as AWX
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: example

short_description: Module for specific live tests

version_added: "2.0.0"

description: This module is part of a test collection in local source.

options:
    host_name:
        description: Name to return as the host name.
        required: false
        type: str

author:
    - AWX Live Tests
'''

EXAMPLES = r'''
- name: Test with defaults
  demo.query.example:

- name: Test with custom host name
  demo.query.example:
    host_name: foo_host
'''

RETURN = r'''
direct_host_name:
    description: The name of the host, this will be collected with the feature.
    type: str
    returned: always
    sample: 'foo_host'
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        host_name=dict(type='str', required=False, default='foo_host_default'),
    )

    result = dict(
        changed=False,
        other_data='sample_string',
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    result['direct_host_name'] = module.params['host_name']
    result['nested_host_name'] = {'host_name': module.params['host_name']}
    result['name'] = 'vm-foo'

    # non-cononical facts
    result['device_type'] = 'Fake Host'

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
