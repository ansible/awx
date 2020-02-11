#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_inventory_source
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: create, update, or destroy Ansible Tower inventory source.
description:
    - Create, update, or destroy Ansible Tower inventory source. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory source.
      required: True
      type: str
    new_name:
      description:
        - A new name for this assets (will rename the asset)
      required: False
      type: str
    description:
      description:
        - The description to use for the inventory source.
      type: str
    inventory:
      description:
        - Inventory the group should be made a member of.
      required: True
      type: str
    source:
      description:
        - The source to use for this group.
      choices: [ "manual", "file", "scm", "ec2", "gce", "azure_rm", "vmware", "satellite6", "cloudforms", "openstack", "rhv", "tower", "custom" ]
      type: str
      required: False
    source_path:
      description:
        - For an SCM based inventory source, the source path points to the file within the repo to use as an inventory.
      type: str
    source_script:
      description:
        - Inventory script to be used when group type is C(custom).
      type: str
      required: False
    source_vars:
      description:
        - The variables or environment fields to apply to this source type.
      type: dict
    credential:
      description:
        - Credential to use for the source.
      type: str
    source_regions:
      description:
        - Regions for cloud provider.
      type: str
    instance_filters:
      description:
        - Comma-separated list of filter expressions for matching hosts.
      type: str
    group_by:
      description:
        - Limit groups automatically created from inventory source.
      type: str
    overwrite:
      description:
        - Delete child groups and hosts not found in source.
      type: bool
      default: 'no'
    overwrite_vars:
      description:
        - Override vars in child groups and hosts with those from external source.
      type: bool
    custom_virtualenv:
      version_added: "2.9"
      description:
        - Local absolute file path containing a custom Python virtualenv to use.
      type: str
      required: False
      default: ''
    timeout:
      description: The amount of time (in seconds) to run before the task is canceled.
      type: int
    verbosity:
      description: The verbosity level to run this inventory source under.
      type: int
      choices: [ 0, 1, 2 ]
    update_on_launch:
      description:
        - Refresh inventory data from its source each time a job is run.
      type: bool
      default: 'no'
    update_cache_timeout:
      description:
        - Time in seconds to consider an inventory sync to be current.
      type: int
    source_project:
      description:
        - Project to use as source with scm option
      type: str
    update_on_project_update:
      description: Update this source when the related project updates if source is C(scm)
      type: bool
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
    tower_oauthtoken:
      description:
        - The Tower OAuth token to use.
      required: False
      type: str
extends_documentation_fragment: awx.awx.auth
'''

EXAMPLES = '''
- name: Add tower group
  tower_group:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ..module_utils.tower_api import TowerModule
from json import dumps


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(type='str'),
        description=dict(),
        inventory=dict(required=True),
        #
        # How do we handle manual and file? Tower does not seem to be able to activate them
        #
        source=dict(choices=["manual", "file", "scm", "ec2", "gce",
                             "azure_rm", "vmware", "satellite6", "cloudforms",
                             "openstack", "rhv", "tower", "custom"], required=False),
        source_path=dict(),
        source_script=dict(required=False),
        source_vars=dict(type='dict'),
        credential=dict(),
        source_regions=dict(),
        instance_filters=dict(),
        group_by=dict(),
        overwrite=dict(type='bool'),
        overwrite_vars=dict(type='bool'),
        custom_virtualenv=dict(type='str'),
        timeout=dict(type='int'),
        verbosity=dict(type='int', choices=[0, 1, 2]),
        update_on_launch=dict(type='bool'),
        update_cache_timeout=dict(type='int'),
        source_project=dict(type='str'),
        update_on_project_update=dict(type='bool'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # One question here is do we want to end up supporting this within the ansible module itself (i.e. required if, etc)
    # Or do we want to let the API return issues with "this dosen't support that", etc.
    #
    # GUI OPTIONS:
    # - - - - - - - manual:	file:	scm:	ec2:	gce	azure_rm	vmware	sat	cloudforms	openstack	rhv	tower	custom
    # credential		?	?	o	o	r	r		r	r	r		r		r	r	o
    # source_project		?	?	r	-	-	-		-	-	-		-		-	-	-
    # source_path		?	?	r	-	-	-		-	-	-		-		-	-	-
    # verbosity			?	?	o	o	o	o		o	o	o		o		o	o	o
    # overwrite			?	?	o	o	o	o		o	o	o		o		o	o	o
    # overwrite_vars		?	?	o	o	o	o		o	o	o		o		o	o	o
    # update_on_launch		?	?	o	o	o	o		o	o	o		o		o	o	o
    # update_on_project_launch	?	?	o	-	-	-		-	-	-		-		-	-	-
    # source_regions		?	?	-	o	o	o		-	-	-		-		-	-	-
    # instance_filters		?	?	-	o	-	-		o	-	-		-		-	o	-
    # group_by			?	?	-	o	-	-		o	-	-		-		-	-	-
    # source_vars*		?	?	-	o	-	o		o	o	o		o		-	-	-
    # environmet vars*		?	?	o	-	-	-		-	-	-		-		-	-	o
    # source_script		?	?	-	-	-	-		-	-	-		-		-	-	r
    #
    # * - source_vars are labeled environment_vars on project and custom sources

    # Create a module for ourselves
    module = TowerModule(argument_spec=argument_spec,
                         supports_check_mode=True,
                         required_if=[
                             # We don't want to require source if state is present because
                             # you might be doing an update to an existing source.
                             # Later on in the code, we will do a test so that if state: present
                             # and if we don't have an object, we must have source.
                             ('source', 'scm', ['source_project', 'source_path']),
                             ('source', 'gce', ['credential']),
                             ('source', 'azure_rm', ['credential']),
                             ('source', 'vmware', ['credential']),
                             ('source', 'satellite6', ['credential']),
                             ('source', 'cloudforms', ['credential']),
                             ('source', 'openstack', ['credential']),
                             ('source', 'rhv', ['credential']),
                             ('source', 'tower', ['credential']),
                             ('source', 'custom', ['source_script']),
                         ],
                         # This is provided by our module, it's not a core thing
                         mutually_exclusive_if=[
                             ('source', 'scm', ['source_regions',
                                                'instance_filters',
                                                'group_by',
                                                'source_script'
                                                ]),
                             ('source', 'ec2', ['source_project',
                                                'source_path',
                                                'update_on_project_launch',
                                                'source_script'
                                                ]),
                             ('source', 'gce', ['source_project',
                                                'source_path',
                                                'update_on_project_launch',
                                                'instance_filters',
                                                'group_by',
                                                'source_vars',
                                                'source_script'
                                                ]),
                             ('source', 'azure_rm', ['source_project',
                                                     'source_path',
                                                     'update_on_project_launch',
                                                     'instance_filters',
                                                     'group_by',
                                                     'source_script'
                                                     ]),
                             ('source', 'vmware', ['source_project', 'source_path', 'update_on_project_launch', 'source_regions', 'source_script']),
                             ('source', 'satellite6', ['source_project',
                                                       'source_path',
                                                       'update_on_project_launch',
                                                       'source_regions',
                                                       'instance_filters',
                                                       'group_by',
                                                       'source_script'
                                                       ]),
                             ('source', 'cloudforms', ['source_project',
                                                       'source_path',
                                                       'update_on_project_launch',
                                                       'source_regions',
                                                       'instance_filters',
                                                       'group_by',
                                                       'source_script'
                                                       ]),
                             ('source', 'openstack', ['source_project',
                                                      'source_path',
                                                      'update_on_project_launch',
                                                      'source_regions',
                                                      'instance_filters',
                                                      'group_by',
                                                      'source_script'
                                                      ]),
                             ('source', 'rhv', ['source_project',
                                                'source_path',
                                                'update_on_project_launch',
                                                'source_regions',
                                                'instance_filters',
                                                'group_by',
                                                'source_vars',
                                                'source_script'
                                                ]),
                             ('source', 'tower', ['source_project',
                                                  'source_path',
                                                  'update_on_project_launch',
                                                  'source_regions',
                                                  'group_by',
                                                  'source_vars',
                                                  'source_script'
                                                  ]),
                             ('source', 'custom', ['source_project',
                                                   'source_path',
                                                   'update_on_project_launch',
                                                   'source_regions',
                                                   'instance_filters',
                                                   'group_by'
                                                   ]),
                         ])

    optional_vars = {}
    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    optional_vars['description'] = module.params.get('description')
    inventory = module.params.get('inventory')
    optional_vars['source'] = module.params.get('source')
    optional_vars['source_path'] = module.params.get('source_path')
    source_script = module.params.get('source_script')
    optional_vars['source_vars'] = module.params.get('source_vars')
    credential = module.params.get('credential')
    optional_vars['source_regions'] = module.params.get('source_regions')
    optional_vars['instance_filters'] = module.params.get('instance_filters')
    optional_vars['group_by'] = module.params.get('group_by')
    optional_vars['overwrite'] = module.params.get('overwrite')
    optional_vars['overwrite_vars'] = module.params.get('overwrite_vars')
    optional_vars['custom_virtualenv'] = module.params.get('custom_virtualenv')
    optional_vars['timeout'] = module.params.get('timeout')
    optional_vars['verbosity'] = module.params.get('verbosity')
    optional_vars['update_on_launch'] = module.params.get('update_on_launch')
    optional_vars['update_cache_timeout'] = module.params.get('update_cache_timeout')
    source_project = module.params.get('source_project')
    optional_vars['update_on_project_update'] = module.params.get('update_on_project_update')
    state = module.params.get('state')

    # Attempt to JSON encode source vars
    if optional_vars['source_vars']:
        optional_vars['source_vars'] = dumps(optional_vars['source_vars'])

    # Attempt to lookup the related items the user specified (these will fail the module if not found)
    inventory_id = module.resolve_name_to_id('inventories', inventory)
    if credential:
        optional_vars['credential'] = module.resolve_name_to_id('credentials', credential)
    if source_project:
        optional_vars['source_project'] = module.resolve_name_to_id('projects', source_project)
    if source_script:
        optional_vars['source_script'] = module.resolve_name_to_id('inventory_scripts', source_script)

    # Attempt to lookup team based on the provided name and org ID
    inventory_source = module.get_one('inventory_sources', **{
        'data': {
            'name': name,
            'inventory': inventory_id,
        }
    })

    # Sanity check on arguments
    if state == 'present' and not inventory_source and not optional_vars['source']:
        module.fail_json(msg="If creating a new inventory source, the source param must be present")

    # Create data to sent to create and update
    inventory_source_fields = {
        'name': new_name if new_name else name,
        'inventory': inventory_id,
    }
    # Layer in all remaining optional information
    for field_name in optional_vars:
        if optional_vars[field_name]:
            inventory_source_fields[field_name] = optional_vars[field_name]

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(inventory_source)
    elif state == 'present':
        # If the state was present we can let the module build or update the existing inventory_source, this will return on its own
        module.create_or_update_if_needed(inventory_source, inventory_source_fields, endpoint='inventory_sources', item_type='inventory source')


if __name__ == '__main__':
    main()
