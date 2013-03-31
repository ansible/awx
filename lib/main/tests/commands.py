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
import os
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

    def setUp(self):
        super(BaseCommandTest, self).setUp()
        self._environ = dict(os.environ.items())

    def tearDown(self):
        super(BaseCommandTest, self).tearDown()
        for k,v in self._environ.items():
            if os.environ.get(k, None) != v:
                os.environ[k] = v
        for k,v in os.environ.items():
            if k not in self._environ.keys():
                del os.environ[k]

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
                if n > 0:
                    variable_data = VariableData.objects.create(data=json.dumps({'ho': 'hum-%d' % x}))
                else:
                    variable_data = None
                host = inventory.hosts.create(name='host-%02d-%02d.example.com' % (n, x),
                                              inventory=inventory,
                                              variable_data=variable_data)
                hosts.append(host)
            self.hosts.extend(hosts)
            groups = []
            for x in xrange(5):
                if n > 0:
                    variable_data = VariableData.objects.create(data=json.dumps({'gee': 'whiz-%d' % x}))
                else:
                    variable_data = None
                group = inventory.groups.create(name='group-%d' % x,
                                                inventory=inventory,
                                                variable_data=variable_data)
                groups.append(group)
                group.hosts.add(hosts[x])
                group.hosts.add(hosts[x + 5])
                if n > 0 and x == 4:
                    group.parents.add(groups[3])
            self.groups.extend(groups)

    def test_without_inventory_id(self):
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=self.hosts[0])
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_list_with_inventory_id_as_argument(self):
        inventory = self.inventories[0]
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  inventory=inventory.pk)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(set(data.keys()),
                         set(inventory.groups.values_list('name', flat=True)))
        # Groups for this inventory should only have hosts, and no group
        # variable data or parent/child relationships.
        for k,v in data.items():
            self.assertTrue(isinstance(v, (list, tuple)))
            group = inventory.groups.get(name=k)
            self.assertEqual(set(v),
                             set(group.hosts.values_list('name', flat=True)))

    def test_list_with_inventory_id_in_environment(self):
        inventory = self.inventories[1]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(set(data.keys()),
                         set(inventory.groups.values_list('name', flat=True)))
        # Groups for this inventory should have hosts, variable data, and one
        # parent/child relationship.
        for k,v in data.items():
            self.assertTrue(isinstance(v, dict))
            group = inventory.groups.get(name=k)
            self.assertEqual(set(v.get('hosts', [])),
                             set(group.hosts.values_list('name', flat=True)))
            if group.variable_data:
                self.assertEqual(v.get('vars', {}),
                                 json.loads(group.variable_data.data))
            if k == 'group-3':
                self.assertEqual(set(v.get('children', [])),
                                 set(group.children.values_list('name', flat=True)))
            else:
                self.assertFalse('children' in v)

    def test_valid_host(self):
        # Host without variable data.
        inventory = self.inventories[0]
        host = inventory.hosts.all()[2]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=host.name)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(data, {})
        # Host with variable data.
        inventory = self.inventories[1]
        host = inventory.hosts.all()[3]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=host.name)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(data, json.loads(host.variable_data.data))

    def test_invalid_host(self):
        # Valid host, but not part of the specified inventory.
        inventory = self.inventories[0]
        host = Host.objects.exclude(inventory=inventory)[0]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=host.name)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})
        # Invalid hostname not in database.
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host='invalid.example.com')
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_with_invalid_inventory_id(self):
        inventory_pks = set(map(lambda x: x.pk, self.inventories))
        invalid_id = [x for x in xrange(9999) if x not in inventory_pks][0]
        os.environ['ACOM_INVENTORY_ID'] = str(invalid_id)
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})
        os.environ['ACOM_INVENTORY_ID'] = 'not_an_int'
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})
        os.environ['ACOM_INVENTORY_ID'] = str(invalid_id)
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=self.hosts[1])
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})
        os.environ['ACOM_INVENTORY_ID'] = 'not_an_int'
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=self.hosts[2])
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_without_list_or_host_argument(self):
        inventory = self.inventories[0]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory')
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_with_both_list_and_host_arguments(self):
        inventory = self.inventories[0]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  host='blah')
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})
    