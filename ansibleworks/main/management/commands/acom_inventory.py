#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import json
from optparse import make_option
import os
from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):

    help = 'Ansible Commander Inventory script'

    option_list = NoArgsCommand.option_list + (
        make_option('-i', '--inventory', dest='inventory_id', type='int',
                    default=0, help='Inventory ID (can also be specified using'
                                    ' ACOM_INVENTORY_ID environment variable)'),
        make_option('--list', action='store_true', dest='list', default=False,
                    help='Return JSON hash of host groups.'),
        make_option('--host', dest='host', default='',
                    help='Return JSON hash of host vars.'),
        make_option('--indent', dest='indent', type='int', default=None,
                    help='Indentation level for pretty printing output'),
    )

    def get_list(self, inventory, indent=None):
        groups = {}
        for group in inventory.groups.all():
            # FIXME: Check if group is active?
            group_info = {
                'hosts': list(group.hosts.values_list('name', flat=True)),
                'children': list(group.children.values_list('name', flat=True)),
            }
            if group.variables:
                group_info['vars'] = group.variables_dict

            group_info = dict(filter(lambda x: bool(x[1]), group_info.items()))
            if group_info.keys() in ([], ['hosts']):
                groups[group.name] = group_info.get('hosts', [])
            else:
                groups[group.name] = group_info
        self.stdout.write(json.dumps(groups, indent=indent))

    def get_host(self, inventory, hostname, indent=None):
        from ansibleworks.main.models import Host
        hostvars = {}
        try:
            # FIXME: Check if active?
            host = inventory.hosts.get(name=hostname)
        except Host.DoesNotExist:
            raise CommandError('Host %s not found in the given inventory' % hostname)
        hostvars = {}
        if host.variables:
            hostvars = host.variables_dict
        self.stdout.write(json.dumps(hostvars, indent=indent))

    def handle_noargs(self, **options):
        try:
            from ansibleworks.main.models import Inventory
            try:
                # Command line argument takes precedence over environment
                # variable.
                inventory_id = int(options.get('inventory_id', 0) or \
                                   os.getenv('ACOM_INVENTORY_ID', 0))
            except ValueError:
                raise CommandError('Inventory ID must be an integer')
            if not inventory_id:
                raise CommandError('No inventory ID specified')
            try:
                inventory = Inventory.objects.get(id=inventory_id)
            except Inventory.DoesNotExist:
                raise CommandError('Inventory with ID %d not found' % inventory_id)
            host = options.get('host', '')
            list_ = options.get('list', False)
            indent = options.get('indent', None)
            if list_ and host:
                raise CommandError('Only one of --list or --host can be specified')
            elif list_:
                self.get_list(inventory, indent=indent)
            elif host:
                self.get_host(inventory, host, indent=indent)
            else:
                raise CommandError('Either --list or --host must be specified')
        except CommandError, e:
            # Always return an empty hash on stdout, even when an error occurs.
            self.stdout.write(json.dumps({}))
            raise

if __name__ == '__main__':
    from __init__ import run_command_as_script
    command_name = os.path.splitext(os.path.basename(__file__))[0]
    run_command_as_script(command_name)
