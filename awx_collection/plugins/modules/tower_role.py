#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_role
author: "Wayne Witzel III (@wwitzel3)"
short_description: grant or revoke an Ansible Tower role.
description:
    - Roles are used for access control, this module is for managing user access to server resources.
    - Grant or revoke Ansible Tower roles to users. See U(https://www.ansible.com/tower) for an overview.
options:
    user:
      description:
        - User that receives the permissions specified by the role.
      type: str
    team:
      description:
        - Team that receives the permissions specified by the role.
      type: str
    role:
      description:
        - The role type to grant/revoke.
      required: True
      choices: ["admin", "read", "member", "execute", "adhoc", "update", "use", "auditor", "project_admin", "inventory_admin", "credential_admin",
                "workflow_admin", "notification_admin", "job_template_admin"]
      type: str
    target_team:
      description:
        - Team that the role acts on.
        - For example, make someone a member or an admin of a team.
        - Members of a team implicitly receive the permissions that the team has.
      type: str
    inventory:
      description:
        - Inventory the role acts on.
      type: str
    job_template:
      description:
        - The job template the role acts on.
      type: str
    workflow:
      description:
        - The workflow job template the role acts on.
      type: str
    credential:
      description:
        - Credential the role acts on.
      type: str
    organization:
      description:
        - Organization the role acts on.
      type: str
    project:
      description:
        - Project the role acts on.
      type: str
    state:
      description:
        - Desired state.
        - State of present indicates the user should have the role.
        - State of absent indicates the user should have the role taken away, if they have it.
      default: "present"
      choices: ["present", "absent"]
      type: str

extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add jdoe to the member role of My Team
  tower_role:
    user: jdoe
    target_team: "My Team"
    role: member
    state: present
'''

from ..module_utils.tower_api import TowerAPIModule


def main():

    argument_spec = dict(
        user=dict(),
        team=dict(),
        role=dict(choices=["admin", "read", "member", "execute", "adhoc", "update", "use", "auditor", "project_admin", "inventory_admin", "credential_admin",
                           "workflow_admin", "notification_admin", "job_template_admin"], required=True),
        target_team=dict(),
        inventory=dict(),
        job_template=dict(),
        workflow=dict(),
        credential=dict(),
        organization=dict(),
        project=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerAPIModule(argument_spec=argument_spec)

    role_type = module.params.pop('role')
    role_field = role_type + '_role'
    state = module.params.pop('state')

    module.json_output['role'] = role_type

    # Lookup data for all the objects specified in params
    params = module.params.copy()
    resource_param_keys = (
        'user', 'team',
        'target_team', 'inventory', 'job_template', 'workflow', 'credential', 'organization', 'project'
    )
    resource_data = {}
    for param in resource_param_keys:
        endpoint = module.param_to_endpoint(param)

        resource_name = params.get(param)
        if resource_name:
            resource = module.get_exactly_one(module.param_to_endpoint(param), resource_name)
            resource_data[param] = resource

    # separate actors from resources
    actor_data = {}
    for key in ('user', 'team'):
        if key in resource_data:
            actor_data[key] = resource_data.pop(key)

    # build association agenda
    associations = {}
    for actor_type, actor in actor_data.items():
        for resource_type, resource in resource_data.items():
            resource_roles = resource['summary_fields']['object_roles']
            if role_field not in resource_roles:
                available_roles = ', '.join(list(resource_roles.keys()))
                module.fail_json(msg='Resource {0} has no role {1}, available roles: {2}'.format(
                    resource['url'], role_field, available_roles
                ), changed=False)
            role_data = resource_roles[role_field]
            endpoint = '/roles/{0}/{1}/'.format(role_data['id'], module.param_to_endpoint(actor_type))
            associations.setdefault(endpoint, [])
            associations[endpoint].append(actor['id'])

    # perform associations
    for association_endpoint, new_association_list in associations.items():
        response = module.get_all_endpoint(association_endpoint)
        existing_associated_ids = [association['id'] for association in response['json']['results']]

        if state == 'present':
            for an_id in list(set(new_association_list) - set(existing_associated_ids)):
                response = module.post_endpoint(association_endpoint, **{'data': {'id': int(an_id)}})
                if response['status_code'] == 204:
                    module.json_output['changed'] = True
                else:
                    module.fail_json(msg="Failed to grant role. {0}".format(response['json'].get('detail', response['json'].get('msg', 'unknown'))))
        else:
            for an_id in list(set(existing_associated_ids) & set(new_association_list)):
                response = module.post_endpoint(association_endpoint, **{'data': {'id': int(an_id), 'disassociate': True}})
                if response['status_code'] == 204:
                    module.json_output['changed'] = True
                else:
                    module.fail_json(msg="Failed to revoke role. {0}".format(response['json'].get('detail', response['json'].get('msg', 'unknown'))))

    module.exit_json(**module.json_output)


if __name__ == '__main__':
    main()
