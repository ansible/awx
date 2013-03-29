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
import StringIO
import sys
from django.core.management import call_command
from django.core.management.base import CommandError
from lib.main.models import *
from lib.main.tests.base import BaseTest

class BaseCommandTest(BaseTest):
    '''
    Base class for tests that run management commands.
    '''

    def run_command(self, name, *args, **options):
        '''
        Run a management command and capture its stdout/stderr along with any
        exceptions.
        '''
        options.setdefault('verbosity', 1)
        options.setdefault('interactive', False)
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
        result = None
        try:
            result = call_command(name, *args, **options)
        except Exception, e:
            result = e
        except SystemExit, e:
            result = e
        finally:
            captured_stdout = sys.stdout.getvalue()
            captured_stderr = sys.stderr.getvalue()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        return result, captured_stdout, captured_stderr

class AcomInventoryTest(BaseCommandTest):
    '''
    Test cases for acom_inventory management command.
    '''

    def setUp(self):
        super(AcomInventoryTest, self).setUp()
        self.setup_users()
        self.organizations = self.make_organizations(self.super_django_user, 2)
        self.projects = self.make_projects(self.normal_django_user, 2)
        self.organizations[0].projects.add(self.projects[1])
        self.organizations[1].projects.add(self.projects[0])
        self.inventories = []
        self.hosts = []
        self.groups = []
        for n, organization in enumerate(self.organizations):
            inventory = Inventory.objects.create(name='inventory-%d' % n,
                                                 description='description for inventory %d' % n,
                                                 organization=organization)
            self.inventories.append(inventory)
            hosts = []
            for x in xrange(10):
                host = inventory.hosts.create(name='host-%02d.example.com' % x,
                                              inventory=inventory)
                hosts.append(host)
            self.hosts.extend(hosts)
            groups = []
            for x in xrange(5):
                group = inventory.groups.create(name='group-%d' % x,
                                                inventory=inventory)
                groups.append(group)
                group.hosts.add(hosts[x])
                group.hosts.add(hosts[x + 5])
            self.groups.extend(groups)

    def test_without_inventory_id(self):
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_with_inventory_id_as_argument(self):
        inventory = self.inventories[0]
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  inventory=inventory.pk)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(set(data.keys()),
                         set(inventory.groups.values_list('name', flat=True)))

    def test_with_inventory_id_in_environment(self):
        pass

    def test_with_invalid_inventory_id(self):
        pass

    