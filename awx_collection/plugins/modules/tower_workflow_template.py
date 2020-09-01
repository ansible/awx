#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['deprecated'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_workflow_template
deprecated:
  removed_in: "14.0.0"
  why: Deprecated in favor of C(_workflow_job_template) and C(_workflow_job_template_node) modules.
  alternative: Use M(tower_workflow_job_template) and M(_workflow_job_template_node) instead.
author: "Adrien Fleury (@fleu42)"
short_description: create, update, or destroy Ansible Tower workflow template.
description:
    - A tower-cli based module for CRUD actions on workflow job templates.
    - Enables use of the old schema functionality.
    - Not updated for new features, convert to the modules for
      workflow_job_template and workflow_job_template node instead.
options:
    allow_simultaneous:
      description:
        - If enabled, simultaneous runs of this job template will be allowed.
      type: bool
    ask_extra_vars:
      description:
        - Prompt user for (extra_vars) on launch.
      type: bool
    ask_inventory:
      description:
        - Prompt user for inventory on launch.
      type: bool
    description:
      description:
        - The description to use for the workflow.
      type: str
    extra_vars:
      description:
        - Extra variables used by Ansible in YAML or key=value format.
      type: dict
    inventory:
      description:
        - Name of the inventory to use for the job template.
      type: str
    name:
      description:
        - The name to use for the workflow.
      required: True
      type: str
    organization:
      description:
        - The organization the workflow is linked to.
      type: str
    schema:
      description:
        - >
          The schema is a JSON- or YAML-formatted string defining the
          hierarchy structure that connects the nodes. Refer to Tower
          documentation for more information.
      type: list
      elements: dict
    survey_enabled:
      description:
        - Setting that variable will prompt the user for job type on the
          workflow launch.
      type: bool
    survey:
      description:
        - The definition of the survey associated to the workflow.
      type: dict
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str

requirements:
- ansible-tower-cli >= 3.0.2

extends_documentation_fragment: awx.awx.auth_legacy
'''


EXAMPLES = '''
- tower_workflow_template:
    name: Workflow Template
    description: My very first Workflow Template
    organization: My optional Organization
    schema: "{{ lookup('file', 'my_workflow.json') }}"

- tower_workflow_template:
    name: Workflow Template
    state: absent
'''


RETURN = ''' # '''


from ..module_utils.tower_legacy import (
    TowerLegacyModule,
    tower_auth_config,
    tower_check_mode
)

import json

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        extra_vars=dict(type='dict'),
        organization=dict(),
        allow_simultaneous=dict(type='bool'),
        schema=dict(type='list', elements='dict'),
        survey=dict(type='dict'),
        survey_enabled=dict(type='bool'),
        inventory=dict(),
        ask_inventory=dict(type='bool'),
        ask_extra_vars=dict(type='bool'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerLegacyModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    module.deprecate(msg=(
        "This module is replaced by the combination of tower_workflow_job_template and "
        "tower_workflow_job_template_node. This uses the old tower-cli and wll be "
        "removed in 2022."
    ), version='awx.awx:14.0.0')

    name = module.params.get('name')
    state = module.params.get('state')

    schema = None
    if module.params.get('schema'):
        schema = module.params.get('schema')

    if schema and state == 'absent':
        module.fail_json(
            msg='Setting schema when state is absent is not allowed',
            changed=False
        )

    json_output = {'workflow_template': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        wfjt_res = tower_cli.get_resource('workflow')
        params = {}
        params['name'] = name

        if module.params.get('description'):
            params['description'] = module.params.get('description')

        if module.params.get('organization'):
            organization_res = tower_cli.get_resource('organization')
            try:
                organization = organization_res.get(
                    name=module.params.get('organization'))
                params['organization'] = organization['id']
            except exc.NotFound as excinfo:
                module.fail_json(
                    msg='Failed to update organization source,'
                    'organization not found: {0}'.format(excinfo),
                    changed=False
                )

        if module.params.get('survey'):
            params['survey_spec'] = module.params.get('survey')

        if module.params.get('ask_extra_vars'):
            params['ask_variables_on_launch'] = module.params.get('ask_extra_vars')

        if module.params.get('ask_inventory'):
            params['ask_inventory_on_launch'] = module.params.get('ask_inventory')

        for key in ('allow_simultaneous', 'inventory',
                    'survey_enabled', 'description'):
            if module.params.get(key):
                params[key] = module.params.get(key)

        # Special treatment for tower-cli extra_vars
        extra_vars = module.params.get('extra_vars')
        if extra_vars:
            params['extra_vars'] = [json.dumps(extra_vars)]

        try:
            if state == 'present':
                params['create_on_missing'] = True
                result = wfjt_res.modify(**params)
                json_output['id'] = result['id']
                if schema:
                    wfjt_res.schema(result['id'], json.dumps(schema))
            elif state == 'absent':
                params['fail_on_missing'] = False
                result = wfjt_res.delete(**params)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update workflow template: \
                    {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
