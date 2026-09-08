#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

# Phase 1 : Collection Import and API Module Initialization


#try:
#    from ansible_collections.ansible.controller.plugins.module_utils.controller_api import ControllerAPIModule
#except ImportError:
#    from ansible_collections.awx.awx.plugins.module_utils.controller_api import ControllerAPIModule

from ansible_collections.ansible.controller.plugins.module_utils.controller_api import ControllerAPIModule

def get_all_items(module, endpoint):
    """
     Get all items from a paginated API endpoint.
    """
    items_map = {}
    current_endpoint = endpoint

    while current_endpoint:

        if current_endpoint.startswith('/api/v2/'):
            current_endpoint = current_endpoint[8:]

        response = module.get_endpoint(current_endpoint)

        if response.get('status_code') not in [200, 201]:
            module.fail_json(msg=f"Failed to retrieve items from endpoint '{current_endpoint}: {response}")
                
        json_data=response.get('json', {})

        for item in json_data.get('results', []):
            items_map[item['name']] = item

        current_endpoint = json_data.get('next', None)
    return items_map

def run_module():

# Phase 2 : Input Schema Definition and Authentication

    element_spec = dict(
        name=dict(type='str', required=True),
       # job_type=dict(type='str', required=False, choices=['run', 'check']),
        inventory=dict(type='str', required=False),
        project=dict(type='str', required=False),
        playbook=dict(type='str', required=False),
    )

# Schema for top level playbook input

    argument_spec = dict(
        job_templates=dict(type='list', elements='dict', options=element_spec, required=True),
        delete_if_missing=dict(type='bool', required=False, default=False),
        exclude_templates=dict(type='list', elements='str', required=False, default=[]),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
    )

# Initialize Controller API module 
    module = ControllerAPIModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    desired_jts = module.params.get('job_templates', [])
    delete_if_missing = module.params.get('delete_if_missing', False)

# Phase 3 : In Memory Mapping of Names to IDs for Projects, Inventories, and Existing Job Templates

    projects_map = get_all_items(module, 'projects')
    inventories_map = get_all_items(module, 'inventories')
    existing_jts_map = get_all_items(module, 'job_templates')

    to_create = []
    to_update = []
    to_delete = []
    unchanged = []
    errors = []
    changed = False

    desired_names = set ()

# Phase 4 : RECONCILIATION Create, Update, Delete, or No Change

    for jt in desired_jts:
        name = jt['name']
        desired_names.add(name)

        payload = { 'name': name }
        item_has_error = False

# Resolve Project Name to ID

        if jt.get('project'):
            if jt['project'] in projects_map:
                payload['project'] = projects_map[jt['project']]['id']
            else:
                errors.append(f"Project '{jt['project']}' not found in AAP")
                item_has_error = True

# Resolve Inventory Name to ID

        if jt.get('inventory'):
            if jt['inventory'] in inventories_map:
                payload['inventory'] = inventories_map[jt['inventory']]['id']
            else:
                errors.append(f"Inventory '{jt['inventory']}' not found in AAP")
                item_has_error = True

        if jt.get('playbook'):
            payload['playbook'] = jt['playbook']

        if item_has_error:
            continue

# Action: Create or Update or Unchanged

        if name not in existing_jts_map:
            changed = True
            to_create.append(name)
            if not module.check_mode:
                res = module.post_endpoint('job_templates', data=payload)
                if res.get('status_code') not in [200, 201]:
                    errors.append(f"Failed to create Job Template '{name}': {res}")

        else:
            existing_jt = existing_jts_map[name]
            jt_id = existing_jt['id']

            has_diff = False
            for key, value in payload.items():
                if existing_jt.get(key) != value:
                    has_diff = True
                    break

            if has_diff:
                changed = True
                to_update.append(name)
                if not module.check_mode:
                    res = module.patch_endpoint(f'job_templates/{jt_id}/', data=payload)
                    if res.get('status_code') not in [200, 202]:
                        errors.append(f"Failed to update Job Template '{name}': {res}")
            else:
                unchanged.append(name)

# Prune unmanaged Job Templates if delete_if_missing is True
    exclude_templates = set(module.params.get('exclude_templates', []))

    if delete_if_missing:
        for existing_name,existing_jt in existing_jts_map.items():
            if existing_name not in desired_names and existing_name not in exclude_templates:
                changed = True
                to_delete.append(existing_name)
                if not module.check_mode:
                    jt_id = existing_jt['id']
                    res = module.delete_endpoint(f'job_templates/{jt_id}/')
                    if res.get('status_code') not in [200, 202, 204]:
                        errors.append(f"Failed to delete Job Template '{existing_name}': {res}")

    if errors:
        module.fail_json(msg="Errors occurred during reconciliation", errors=errors)

# Return the result

    module.exit_json(
        changed=changed,
        msg="Bulk Reconciliation completed successfully",
        templates_to_create=to_create,
        templates_to_update=to_update,
        templates_to_delete=to_delete,
        unchanged=unchanged,
        check_mode=module.check_mode
    )

def main():
    run_module()


if __name__ == '__main__':
    main()
