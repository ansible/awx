#!/usr/bin/env python

from ansible.module_utils.basic import * # noqa

DOCUMENTATION = '''
---
module: set_artifact
short_description: Stash some Ansible variables for later
description:
    - Saves a user-specified JSON dictionary of variables from a playbook
      for later use
version_added: "2.2"
options:
requirements: [ ]
author: Alan Rominger
'''

EXAMPLES = '''
# Example fact output:

# Simple specifying of an artifact dictionary, will be passed on callback
- set_artifact:
    data:
        one_artifact: "{{ local_var * 2 }}"
        another_artifact: "{{ some_registered_var.results | map(attribute='ansible_facts.some_fact') | list }}"


# Specifying a local path to save the artifacts to
- set_artifact:
    data:
        one_artifact: "{{ local_var * 2 }}"
        another_artifact: "{{ some_registered_var.results | map(attribute='ansible_facts.some_fact') | list }}"
    dest=/tmp/prefix-{{ inventory_hostname }}



host | success >> {
    "artifact_data": {}
}
'''

def main():
    import json
    module = AnsibleModule(
        argument_spec = dict(
            data=dict(
                type='dict',
                default={}
            )
        )
    )
    results = dict(
        changed=True,
        artifact_data=json.dumps(module.params.get('data'))
    )
    module.exit_json(**results)

if __name__ == '__main__':
    main()
