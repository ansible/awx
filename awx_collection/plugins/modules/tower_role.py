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
      choices: ["admin", "read", "member", "execute", "adhoc", "update", "use", "approval", "auditor", "project_admin", "inventory_admin", "credential_admin",
                "workflow_admin", "notification_admin", "job_template_admin"]
      type: str
    target_team:
      description:
        - Team that the role acts on.
        - For example, make someone a member or an admin of a team.
        - Members of a team implicitly receive the permissions that the team has.
        - Deprecated, use 'target_teams'.
      type: str
    target_teams:
      description:
        - Team that the role acts on.
        - For example, make someone a member or an admin of a team.
        - Members of a team implicitly receive the permissions that the team has.
      type: list
      elements: str
    inventory:
      description:
        - Inventory the role acts on.
        - Deprecated, use 'inventories'.
      type: str
    inventories:
      description:
        - Inventory the role acts on.
      type: list
      elements: str
    job_template:
      description:
        - The job template the role acts on.
        - Deprecated, use 'job_templates'.
      type: str
    job_templates:
      description:
        - The job template the role acts on.
      type: list
      elements: str
    workflow:
      description:
        - The workflow job template the role acts on.
        - Deprecated, use 'workflows'.
      type: str
    workflows:
      description:
        - The workflow job template the role acts on.
      type: list
      elements: str
    credential:
      description:
        - Credential the role acts on.
        - Deprecated, use 'credentials'.
      type: str
    credentials:
      description:
        - Credential the role acts on.
      type: list
      elements: str
    organization:
      description:
        - Organization the role acts on.
        - Deprecated, use 'organizations'.
      type: str
    organizations:
      description:
        - Organization the role acts on.
      type: list
      elements: str
    lookup_organization:
      description:
        - Organization the inventories, job templates, projects, or workflows the items exists in.
        - Used to help lookup the object, for organization roles see organization.
        - If not provided, will lookup by name only, which does not work with duplicates.
      type: str
    project:
      description:
        - Project the role acts on.
        - Deprecated, use 'projects'.
      type: str
    projects:
      description:
        - Project the role acts on.
      type: list
      elements: str
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

- name: Add Joe to multiple job templates and a workflow
  tower_role:
    user: joe
    role: execute
    workflow: test-role-workflow
    job_templates:
      - jt1
      - jt2
    state: present
'''

from ..module_utils.tower_api import TowerAPIModule


def main():

    argument_spec = dict(
        user=dict(),
        team=dict(),
        role=dict(choices=["admin", "read", "member", "execute", "adhoc", "update", "use", "approval",
                           "auditor", "project_admin", "inventory_admin", "credential_admin",
                           "workflow_admin", "notification_admin", "job_template_admin"], required=True),
        target_team=dict(),
        target_teams=dict(type='list', elements='str'),
        inventory=dict(),
        inventories=dict(type='list', elements='str'),
        job_template=dict(),
        job_templates=dict(type='list', elements='str'),
        workflow=dict(),
        workflows=dict(type='list', elements='str'),
        credential=dict(),
        credentials=dict(type='list', elements='str'),
        organization=dict(),
        organizations=dict(type='list', elements='str'),
        lookup_organization=dict(),
        project=dict(),
        projects=dict(type='list', elements='str'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerAPIModule(argument_spec=argument_spec)

    role_type = module.params.pop('role')
    role_field = role_type + '_role'
    state = module.params.pop('state')

    module.json_output['role'] = role_type

    # Deal with legacy parameters
    resource_list_param_keys = {
        'credentials': 'credential',
        'inventories': 'inventory',
        'job_templates': 'job_template',
        'organizations': 'organization',
        'projects': 'project',
        'target_teams': 'target_team',
        'workflows': 'workflow'
    }
    # Singular parameters
    resource_param_keys = (
        'user', 'team', 'lookup_organization'
    )

    resources = {}
    for resource_group in resource_list_param_keys:
        if module.params.get(resource_group) is not None:
            resources.setdefault(resource_group, []).extend(module.params.get(resource_group))
        if module.params.get(resource_list_param_keys[resource_group]) is not None:
            resources.setdefault(resource_group, []).append(module.params.get(resource_list_param_keys[resource_group]))
    for resource_group in resource_param_keys:
        if module.params.get(resource_group) is not None:
            resources[resource_group] = module.params.get(resource_group)
    # Change workflows and target_teams key to its endpoint name.
    if 'workflows' in resources:
        resources['workflow_job_templates'] = resources.pop('workflows')
    if 'target_teams' in resources:
        resources['teams'] = resources.pop('target_teams')

    # Set lookup data to use
    lookup_data = {}
    if 'lookup_organization' in resources:
        lookup_data['organization'] = module.resolve_name_to_id('organizations', resources['lookup_organization'])
        resources.pop('lookup_organization')

    # Lookup actor data
    # separate actors from resources
    actor_data = {}
    for key in ('user', 'team'):
        if key in resources:
            if key == 'user':
                lookup_data_populated = {}
            else:
                lookup_data_populated = lookup_data
            # Attempt to look up project based on the provided name or ID and lookup data
            actor_data[key] = module.get_one('{0}s'.format(key), name_or_id=resources[key], data=lookup_data_populated)
            resources.pop(key)

    # Lookup Resources
    resource_data = {}
    for key in resources:
        for resource in resources[key]:
            # Attempt to look up project based on the provided name or ID and lookup data
            if key in resources:
                if key == 'organizations':
                    lookup_data_populated = {}
                else:
                    lookup_data_populated = lookup_data

            resource_data.setdefault(key, []).append(module.get_one(key, name_or_id=resource, data=lookup_data_populated))

    # build association agenda
    associations = {}
    for actor_type, actor in actor_data.items():
        for key in resource_data:
            for resource in resource_data[key]:
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
