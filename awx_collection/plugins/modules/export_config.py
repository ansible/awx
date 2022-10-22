#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2021, Sean Sullivan
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: export_config
author: "Sean Sullivan (@sean-m-sullivan)"
short_description: export cassets with associations from Automation Platform Controller.
description:
    - Export assets with associations from Automation Platform Controller.
options:
    endpoints:
      description:
        - list of endpoints to export
      type: list
      elements: str
    search_fields:
      description:
        - The fields to use to narrow down search results.
        - This is likely organization, however it does accept other fields
      type: list
      elements: dict
    raw:
      description:
        - Export raw output without processing.
      type: bool
notes:
  - Specifying a name of "all" for any asset type will export all items of that asset type.
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Export all assets
  export:
    all: True

- name: Export all inventories
  export:
    inventory: 'all'

- name: Export a job template named "My Template" and all Credentials
  export:
    job_templates: "My Template"
    credential: 'all'
'''

from ..module_utils.controller_api import ControllerAPIModule


def nested_get(module, dic, keys):    
    for key in keys:
        dic = dic[key]
    return dic


def resolve_dict_associations(module, data, type):
    models = {
      'credential': {
        'organization': ["summary_fields", "organization", "name"],
        'credential_type': ["summary_fields", "credential_type", "name"],
        'name': ['name'],
      },
      'inventory': {
        'organization': ["summary_fields", "organization", "name"],
        'name': ['name'],
      }
    }
    response = {}
    for key, value in models[type].items():
        response[key] = nested_get(module, data, value)
    return response


def resolve_associations(module, response, endpoint):
    summary_fields = {
      'credentials': {
        'credential_type': 'name',
      },
      'execution_environments': {
        'credential': 'name',
      },
    }
    related_fields = {
      'credential_input_sources': {
        'dicts': {
          'source_credential': 'credential',
          'target_credential': 'credential',
        },
      },
      'groups': {
        'dicts': {
          'inventory': 'inventory',
        }
      },
      'hosts': {
        'dicts': {
          'inventory': 'inventory',
        }
      },
    }


    for index, list_item in enumerate(response):
      # add organization to summary fields
      if endpoint not in summary_fields:
          summary_fields[endpoint] = {'organization': 'name'}
      else:
          summary_fields[endpoint].update({'organization': 'name'})

      # Resolve lookups that can be done with summary fields.
      if endpoint in summary_fields:
          for key, value in summary_fields[endpoint].items():
              if key in list_item and list_item[key] is not None:
                  response[index][key] = list_item['summary_fields'][key][value]

      # Resolve lookups that can be done with summary fields.
      if endpoint in related_fields:
          if 'dicts' in related_fields[endpoint]:
              for key, value in related_fields[endpoint]['dicts'].items():
                  response[index][key] = resolve_dict_associations(module, module.get_endpoint(list_item['related'][key])['json'], value)

      # Exceptions
      if endpoint == 'credentials':
          for owner in list_item['summary_fields']['owners']:
              if owner['type'] == 'user':
                  response[index].setdefault('users', []).append(owner['name'])
              if owner['type'] == 'team':
                  response[index].setdefault('teams', []).append(owner['name'])
    return response


def main():
    argument_spec = dict(
        endpoints=dict(type='list', required=True, elements='str'),
        raw=dict(type='bool', default=False),
        search_fields=dict(type='list', elements='dict'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)
    # The export process will never change the AWX system
    module.json_output['changed'] = False

    endpoints = module.params.get('endpoints')
    
    raw = module.params.get('raw')
    search_fields = None
    lookup_data = {}
    if module.params.get('search_fields'):
        search_fields = module.params.get('search_fields')
        for list_field in search_fields:
            for key, value in list_field.items():
              lookup_id = module.get_one(module.param_to_endpoint(key), name_or_id=value)['id']
              lookup_data[key] = lookup_id
    module.json_output['lookup_data'] = lookup_data
    for endpoint in endpoints:
        response = module.get_all_filtered(endpoint, **{'data': lookup_data})
        output_name = 'controller_' + endpoint
        if raw:
            module.json_output[output_name] = response
        else:
            module.json_output[output_name] = resolve_associations(module, response, endpoint)

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
