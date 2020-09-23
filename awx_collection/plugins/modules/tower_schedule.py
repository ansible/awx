#!/usr/bin/python
# coding: utf-8 -*-


# (c) 2020, John Westcott IV <john.westcott.iv@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_schedule
author: "John Westcott IV (@john-westcott-iv)"
short_description: create, update, or destroy Ansible Tower schedules.
description:
    - Create, update, or destroy Ansible Tower schedules. See
      U(https://www.ansible.com/tower) for an overview.
options:
    rrule:
      description:
        - A value representing the schedules iCal recurrence rule.
        - See rrule plugin for help constructing this value
      required: False
      type: str
    name:
      description:
        - Name of this schedule.
      required: True
      type: str
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      required: False
      type: str
    description:
      description:
        - Optional description of this schedule.
      required: False
      type: str
    extra_data:
      description:
        - Specify C(extra_vars) for the template.
      required: False
      type: dict
      default: {}
    inventory:
      description:
        - Inventory applied as a prompt, assuming job template prompts for inventory
      required: False
      type: str
    scm_branch:
      description:
        - Branch to use in job run. Project default used if blank. Only allowed if project allow_override field is set to true.
      required: False
      type: str
    job_type:
      description:
        - The job type to use for the job template.
      required: False
      type: str
      choices:
        - 'run'
        - 'check'
    job_tags:
      description:
        - Comma separated list of the tags to use for the job template.
      required: False
      type: str
    skip_tags:
      description:
        - Comma separated list of the tags to skip for the job template.
      required: False
      type: str
    limit:
      description:
        - A host pattern to further constrain the list of hosts managed or affected by the playbook
      required: False
      type: str
    diff_mode:
      description:
        - Enable diff mode for the job template.
      required: False
      type: bool
    verbosity:
      description:
        - Control the output level Ansible produces as the playbook runs. 0 - Normal, 1 - Verbose, 2 - More Verbose, 3 - Debug, 4 - Connection Debug.
      required: False
      type: int
      choices:
        - 0
        - 1
        - 2
        - 3
        - 4
        - 5
    unified_job_template:
      description:
        - Name of unified job template to schedule.
      required: False
      type: str
    enabled:
      description:
        - Enables processing of this schedule.
      required: False
      type: bool
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Build a schedule for Demo Job Template
  tower_schedule:
    name: "{{ sched1 }}"
    state: present
    unified_job_template: "Demo Job Template"
    rrule: "DTSTART:20191219T130551Z RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=1"
  register: result

- name: Build the same schedule using the rrule plugin
  tower_schedule:
    name: "{{ sched1 }}"
    state: present
    unified_job_template: "Demo Job Template"
    rrule: "{{ query('awx.awx.tower_schedule_rrule', 'week', start_date='2019-12-19 13:05:51') }}"
  register: result
'''

from ..module_utils.tower_api import TowerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        rrule=dict(),
        name=dict(required=True),
        new_name=dict(),
        description=dict(),
        extra_data=dict(type='dict'),
        inventory=dict(),
        scm_branch=dict(),
        job_type=dict(choices=['run', 'check']),
        job_tags=dict(),
        skip_tags=dict(),
        limit=dict(),
        diff_mode=dict(type='bool'),
        verbosity=dict(type='int', choices=[0, 1, 2, 3, 4, 5]),
        unified_job_template=dict(),
        enabled=dict(type='bool'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = TowerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    rrule = module.params.get('rrule')
    name = module.params.get('name')
    new_name = module.params.get("new_name")
    description = module.params.get('description')
    extra_data = module.params.get('extra_data')
    inventory = module.params.get('inventory')
    scm_branch = module.params.get('scm_branch')
    job_type = module.params.get('job_type')
    job_tags = module.params.get('job_tags')
    skip_tags = module.params.get('skip_tags')
    limit = module.params.get('limit')
    diff_mode = module.params.get('diff_mode')
    verbosity = module.params.get('verbosity')
    unified_job_template = module.params.get('unified_job_template')
    enabled = module.params.get('enabled')
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    inventory_id = None
    if inventory:
        inventory_id = module.resolve_name_to_id('inventories', inventory)
    unified_job_template_id = None
    if unified_job_template:
        unified_job_template_id = module.resolve_name_to_id('unified_job_templates', unified_job_template)

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one('schedules', name_or_id=name)

    # Create the data that gets sent for create and update
    new_fields = {}
    if rrule is not None:
        new_fields['rrule'] = rrule
    new_fields['name'] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    if description is not None:
        new_fields['description'] = description
    if extra_data is not None:
        new_fields['extra_data'] = extra_data
    if inventory is not None:
        new_fields['inventory'] = inventory_id
    if scm_branch is not None:
        new_fields['scm_branch'] = scm_branch
    if job_type is not None:
        new_fields['job_type'] = job_type
    if job_tags is not None:
        new_fields['job_tags'] = job_tags
    if skip_tags is not None:
        new_fields['skip_tags'] = skip_tags
    if limit is not None:
        new_fields['limit'] = limit
    if diff_mode is not None:
        new_fields['diff_mode'] = diff_mode
    if verbosity is not None:
        new_fields['verbosity'] = verbosity
    if unified_job_template is not None:
        new_fields['unified_job_template'] = unified_job_template_id
    if enabled is not None:
        new_fields['enabled'] = enabled

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)
    elif state == 'present':
        # If the state was present and we can let the module build or update the existing item, this will return on its own
        module.create_or_update_if_needed(
            existing_item, new_fields,
            endpoint='schedules', item_type='schedule',
            associations={
            }
        )


if __name__ == '__main__':
    main()
