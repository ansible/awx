#!/usr/bin/env python

# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.


import json
from optparse import make_option
import os
import sys
from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):

    help = 'Ansible Commander Inventory script'

    option_list = NoArgsCommand.option_list + (
        make_option('-i', '--inventory', dest='inventory', type='int', default=0,
                    help='Inventory ID (can also be specified using '
                         'ACOM_INVENTORY environment variable)'),
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
            if group.variables is not None:
                group_info['vars'] = json.loads(group.variables.data)

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
        if host.variables is not None:
            hostvars = json.loads(host.variables.data)
        # FIXME: Do we also need to include variables defined for groups of which
        # this host is a member?  (MPD: pretty sure we don't!)
        self.stdout.write(json.dumps(hostvars, indent=indent))

    def handle_noargs(self, **options):
        from lib.main.models import Inventory
        try:
            inventory_id = int(os.getenv('ACOM_INVENTORY', options.get('inventory', 0)))
        except ValueError:
            raise CommandError('Inventory ID must be an integer')
        if not inventory_id:
            raise CommandError('No inventory ID specified')
        try:
            inventory = Inventory.objects.get(id=inventory_id)
        except Inventory.DoesNotExist:
            raise CommandError('Inventory with ID %d not found' % inventory_id)
        list_ = options.get('list', False)
        host = options.get('host', '')
        indent = options.get('indent', None)
        if list_ and host:
            raise CommandError('Only one of --list or --host can be specified')
        elif list_:
            self.get_list(inventory, indent=indent)
        elif host:
            self.get_host(inventory, host, indent=indent)
        else:
            self.stderr.write('Either --list or --host must be specified')
            self.print_help()

if __name__ == '__main__':
    # FIXME: This environment variable *should* already be set if this script
    # is called from a celery task.  Probably won't work otherwise.
    try:
        import lib.settings
    except ImportError:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lib.settings')
    from django.core.management import execute_from_command_line
    argv = [sys.argv[0], 'acom_inventory'] + sys.argv[1:]
    execute_from_command_line(argv)
