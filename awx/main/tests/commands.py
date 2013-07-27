# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import os
import StringIO
import sys
import tempfile
import time

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.timezone import now

# AWX
from awx.main.licenses import LicenseWriter
from awx.main.models import *
from awx.main.tests.base import BaseTest

__all__ = ['CleanupDeletedTest', 'InventoryImportTest']

TEST_INVENTORY_INI = '''\
[webservers]
web1.example.com
web2.example.com
web3.example.com

[webservers:vars]
webvar=blah

[dbservers]
db1.example.com
db2.example.com

[dbservers:vars]
dbvar=ugh

[servers:children]
webservers
dbservers

[servers:vars]
varb=B

[all:vars]
vara=A
'''

class BaseCommandTest(BaseTest):
    '''
    Base class for tests that run management commands.
    '''

    def setUp(self):
        super(BaseCommandTest, self).setUp()
        self._sys_path = [x for x in sys.path]
        self._environ = dict(os.environ.items())
        self._temp_files = []

    def tearDown(self):
        super(BaseCommandTest, self).tearDown()
        sys.path = self._sys_path
        for k,v in self._environ.items():
            if os.environ.get(k, None) != v:
                os.environ[k] = v
        for k,v in os.environ.items():
            if k not in self._environ.keys():
                del os.environ[k]
        for tf in self._temp_files:
            if os.path.exists(tf):
                os.remove(tf)

    def create_test_inventories(self):
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
                                                 organization=organization,
                                                 variables=json.dumps({'n': n}) if n else '')
            self.inventories.append(inventory)
            hosts = []
            for x in xrange(10):
                if n > 0:
                    variables = json.dumps({'ho': 'hum-%d' % x})
                else:
                    variables = ''
                host = inventory.hosts.create(name='host-%02d-%02d.example.com' % (n, x),
                                              inventory=inventory,
                                              variables=variables)
                hosts.append(host)
            self.hosts.extend(hosts)
            groups = []
            for x in xrange(5):
                if n > 0:
                    variables = json.dumps({'gee': 'whiz-%d' % x})
                else:
                    variables = ''
                group = inventory.groups.create(name='group-%d' % x,
                                                inventory=inventory,
                                                variables=variables)
                groups.append(group)
                group.hosts.add(hosts[x])
                group.hosts.add(hosts[x + 5])
                if n > 0 and x == 4:
                    group.parents.add(groups[3])
            self.groups.extend(groups)


    def run_command(self, name, *args, **options):
        '''
        Run a management command and capture its stdout/stderr along with any
        exceptions.
        '''
        command_runner = options.pop('command_runner', call_command)
        stdin_fileobj = options.pop('stdin_fileobj', None)
        options.setdefault('verbosity', 1)
        options.setdefault('interactive', False)
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        if stdin_fileobj:
            sys.stdin = stdin_fileobj
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
        result = None
        try:
            result = command_runner(name, *args, **options)
        except Exception, e:
            result = e
        except SystemExit, e:
            result = e
        finally:
            captured_stdout = sys.stdout.getvalue()
            captured_stderr = sys.stderr.getvalue()
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        # For Django 1.4.x, convert sys.exit(1) and stderr message to the
        # CommandError(msg) exception used by Django 1.5 and later.
        if isinstance(result, SystemExit) and captured_stderr:
            result = CommandError(captured_stderr)
        return result, captured_stdout, captured_stderr

class CleanupDeletedTest(BaseCommandTest):
    '''
    Test cases for cleanup_deleted management command.
    '''

    def setUp(self):
        super(CleanupDeletedTest, self).setUp()
        self.create_test_inventories()

    def get_model_counts(self):
        def get_models(m):
            if not m._meta.abstract:
                yield m
            for sub in m.__subclasses__():
                for subm in get_models(sub):
                    yield subm
        counts = {}
        for model in get_models(PrimordialModel):
            active = model.objects.filter(active=True).count()
            inactive = model.objects.filter(active=False).count()
            counts[model] = (active, inactive)
        return counts

    def test_cleanup_our_models(self):
        # Test with nothing to be deleted.
        counts_before = self.get_model_counts()
        self.assertFalse(sum(x[1] for x in counts_before.values()))
        result, stdout, stderr = self.run_command('cleanup_deleted')
        self.assertEqual(result, None)
        counts_after = self.get_model_counts()
        self.assertEqual(counts_before, counts_after)
        # "Delete" some hosts.
        for host in Host.objects.all():
            host.mark_inactive()
        # With no parameters, "days" defaults to 90, which won't cleanup any of
        # the hosts we just removed.
        counts_before = self.get_model_counts()
        self.assertTrue(sum(x[1] for x in counts_before.values()))
        result, stdout, stderr = self.run_command('cleanup_deleted')
        self.assertEqual(result, None)
        counts_after = self.get_model_counts()
        self.assertEqual(counts_before, counts_after)
        # Even with days=1, the hosts will remain.
        counts_before = self.get_model_counts()
        self.assertTrue(sum(x[1] for x in counts_before.values()))
        result, stdout, stderr = self.run_command('cleanup_deleted', days=1)
        self.assertEqual(result, None)
        counts_after = self.get_model_counts()
        self.assertEqual(counts_before, counts_after)
        # With days=0, the hosts will be deleted.
        counts_before = self.get_model_counts()
        self.assertTrue(sum(x[1] for x in counts_before.values()))
        result, stdout, stderr = self.run_command('cleanup_deleted', days=0)
        self.assertEqual(result, None)
        counts_after = self.get_model_counts()
        self.assertNotEqual(counts_before, counts_after)
        self.assertFalse(sum(x[1] for x in counts_after.values()))

    def get_user_counts(self):
        active = User.objects.filter(is_active=True).count()
        inactive = User.objects.filter(is_active=False).count()
        return active, inactive

    def test_cleanup_user_model(self):
        # Test with nothing to be deleted.
        counts_before = self.get_user_counts()
        self.assertFalse(counts_before[1])
        result, stdout, stderr = self.run_command('cleanup_deleted')
        self.assertEqual(result, None)
        counts_after = self.get_user_counts()
        self.assertEqual(counts_before, counts_after)
        # "Delete some users".
        for user in User.objects.all():
            user.mark_inactive()
        # With days=1, no users will be deleted.
        counts_before = self.get_user_counts()
        self.assertTrue(counts_before[1])
        result, stdout, stderr = self.run_command('cleanup_deleted', days=1)
        self.assertEqual(result, None)
        counts_after = self.get_user_counts()
        self.assertEqual(counts_before, counts_after)
        # With days=0, inactive users will be deleted.
        counts_before = self.get_user_counts()
        self.assertTrue(counts_before[1])
        result, stdout, stderr = self.run_command('cleanup_deleted', days=0)
        self.assertEqual(result, None)
        counts_after = self.get_user_counts()
        self.assertNotEqual(counts_before, counts_after)
        self.assertFalse(counts_after[1])

class InventoryImportTest(BaseCommandTest):
    '''
    Test cases for inventory_import management command.
    '''

    def setUp(self):
        super(InventoryImportTest, self).setUp()
        self.create_test_inventories()
        self.create_test_ini()
        self.create_test_license_file()

    def create_test_license_file(self):
        writer = LicenseWriter( 
           company_name='AWX',
           contact_name='AWX Admin',
           contact_email='awx@example.com',
           license_date=int(time.time() + 3600),
           instance_count=500,
        )
        handle, license_path = tempfile.mkstemp(suffix='.json')
        os.close(handle)
        writer.write_file(license_path)
        self._temp_files.append(license_path)
        os.environ['AWX_LICENSE_FILE'] = license_path

    def create_test_ini(self):
        handle, self.ini_path = tempfile.mkstemp(suffix='.txt')
        ini_file = os.fdopen(handle, 'w')
        ini_file.write(TEST_INVENTORY_INI)
        ini_file.close()
        self._temp_files.append(self.ini_path)

    def test_invalid_options(self):
        inventory_id = self.inventories[0].pk
        inventory_name = self.inventories[0].name
        # No options specified.
        result, stdout, stderr = self.run_command('inventory_import')
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('inventory-id' in str(result))
        self.assertTrue('required' in str(result))
        # Both inventory ID and name.
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=inventory_id,
                                                  inventory_name=inventory_name)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('inventory-id' in str(result))
        self.assertTrue('exclusive' in str(result))
        # Inventory ID with overwrite and keep_vars.
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=inventory_id,
                                                  overwrite=True, keep_vars=True)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('overwrite-vars' in str(result))
        self.assertTrue('exclusive' in str(result))
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=inventory_id,
                                                  overwrite_vars=True,
                                                  keep_vars=True)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('overwrite-vars' in str(result))
        self.assertTrue('exclusive' in str(result))
        # Inventory ID, but no source.
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=inventory_id)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('--source' in str(result))
        self.assertTrue('required' in str(result))
        # Inventory ID, with invalid source.
        invalid_source = ''.join([os.path.splitext(self.ini_path)[0] + '-invalid',
                                  os.path.splitext(self.ini_path)[1]]) 
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=inventory_id,
                                                  source=invalid_source)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('not exist' in str(result))
        # Invalid inventory ID.
        invalid_id = Inventory.objects.order_by('-pk')[0].pk + 1
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=invalid_id,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('matched' in str(result))
        # Invalid inventory name.
        invalid_name = 'invalid inventory name'
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_name=invalid_name,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('matched' in str(result))

    def test_ini_file(self):
        # New empty inventory.
        new_inv = self.organizations[0].inventories.create(name='newb')
        self.assertEqual(new_inv.hosts.count(), 0)
        self.assertEqual(new_inv.groups.count(), 0)
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertEqual(result, None)
        # FIXME

    def test_executable_file(self):
        pass
        # FIXME
