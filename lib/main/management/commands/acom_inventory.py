#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.


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
            if group.variable_data is not None:
                group_info['vars'] = json.loads(group.variable_data.data)

            group_info = dict(filter(lambda x: bool(x[1]), group_info.items()))
            if group_info.keys() in ([], ['hosts']):
                groups[group.name] = group_info.get('hosts', [])
            else:
                groups[group.name] = group_info
        self.stdout.write(json.dumps(groups, indent=indent))

    def get_host(self, inventory, hostname, indent=None):
        from lib.main.models import Host
        hostvars = {}
        try:
            # FIXME: Check if active?
            host = inventory.hosts.get(name=hostname)
        except Host.DoesNotExist:
            raise CommandError('Host %s not found in the given inventory' % hostname)
        hostvars = {}
        if host.variable_data is not None:
            hostvars = json.loads(host.variable_data.data)
        self.stdout.write(json.dumps(hostvars, indent=indent))

    def handle_noargs(self, **options):
        try:
            from lib.main.models import Inventory
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
