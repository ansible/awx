#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


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
                         'ACOM_INVENTORY_ID environment variable)'),
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
                inventory_id = int(os.getenv('ACOM_INVENTORY_ID', options.get('inventory', 0)))
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
    # FIXME: The DJANGO_SETTINGS_MODULE environment variable *should* already
    # be set if this script is called from a celery task.
    settings_module_name = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lib.settings')
    # FIXME: Not particularly fond of this sys.path hack, but it is needed
    # when a celery task calls ansible-playbook and needs to execute this
    # script directly.
    try:
        settings_parent_module = __import__(settings_module_name)
    except ImportError:
        top_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
        sys.path.insert(0, os.path.abspath(top_dir))
        settings_parent_module = __import__(settings_module_name)
    settings_module = getattr(settings_parent_module, settings_module_name.split('.')[-1])
    # Use the ACOM_TEST_DATABASE_NAME environment variable to specify the test
    # database name when called from unit tests.
    if os.environ.get('ACOM_TEST_DATABASE_NAME', None):
        settings_module.DATABASES['default']['NAME'] = os.environ['ACOM_TEST_DATABASE_NAME']
    from django.core.management import execute_from_command_line
    argv = [sys.argv[0], 'acom_inventory'] + sys.argv[1:]
    execute_from_command_line(argv)
