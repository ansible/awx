#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020, Ansible by Red Hat, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_meta
author: "Alan Rominger (@alancoding)"
short_description: Returns metadata about the collection this module lives in.
description:
    - Allows a user to find out what collection this module exists in.
    - This takes common module parameters, but does nothing with them.
options: {}
extends_documentation_fragment: awx.awx.auth
'''


RETURN = '''
prefix:
    description: Collection namespace and name in the namespace.name format
    returned: success
    sample: awx.awx
    type: str
name:
    description: Collection name
    returned: success
    sample: awx
    type: str
namespace:
    description: Collection namespace
    returned: success
    sample: awx
    type: str
version:
    description: Version of the collection
    returned: success
    sample: 0.0.1-devel
    type: str
'''


EXAMPLES = '''
- tower_meta:
  register: result

- name: Show details about the collection
  debug: var=result

- name: Load the UI setting without hard-coding the collection name
  debug:
    msg: "{{ lookup(result.prefix + '.tower_api', 'settings/ui') }}"
'''


from ..module_utils.tower_api import TowerAPIModule


def main():
    module = TowerAPIModule(argument_spec={})
    namespace = {
        'awx': 'awx',
        'tower': 'ansible'
    }.get(module._COLLECTION_TYPE, 'unknown')
    namespace_name = '{0}.{1}'.format(namespace, module._COLLECTION_TYPE)
    module.exit_json(
        prefix=namespace_name,
        name=module._COLLECTION_TYPE,
        namespace=namespace,
        version=module._COLLECTION_VERSION
    )


if __name__ == '__main__':
    main()
