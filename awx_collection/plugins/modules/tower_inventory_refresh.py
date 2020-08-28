#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2020, FERREIRA Christophe <christophe.ferreira@cnaf.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_inventory_refresh
author: "FERREIRA Christophe"
short_description: create, update, or destroy Ansible Tower inventory.
description:
    - Refresh all source in inventory
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory.
      required: True
      type: str
    organization:
      required: False
      description:
        - Organization the job template exists in.
        - Used to help lookup the object, cannot be modified using this module.
        - The Organization is inferred from the associated project
        - If not provided, will lookup by name only, which does not work with duplicates.
        - Requires Tower Version 3.7.0 or AWX 10.0.0 IS NOT backwards compatible with earlier versions.
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Refresh all source in inventory
  tower_inventory_refresh:
    name: "Foo Inventory"
    organization: "Default"
    tower_config_file: "~/tower_cli.cfg"
'''


from ..module_utils.tower_api import TowerAPIModule
import json


def main():

    argument_spec = dict(
        name=dict(required=True),
        organization=dict()
    )

    module = TowerAPIModule(argument_spec=argument_spec)

    name = module.params.get('name')

    lookup_data = {
        'name': name
    }

    if organization:
        org_id = module.resolve_name_to_id('organizations', organization)
        lookup_data['organization'] = org_id

    inventory = module.get_one('inventories', **{'data': lookup_data})

    if inventory == None:
         module.fail_json(msg="Unable to find inventory by name {0}".format(name))

    inventory_id = module.resolve_name_to_id('inventories', name)

    endpoint = '/inventories/' + str(inventory_id) + '/update_inventory_sources/'

    module.post_endpoint(endpoint)

    json_output = dict()
    json_output['changed'] = True

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
