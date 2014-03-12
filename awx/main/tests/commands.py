# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import os
import shutil
import string
import StringIO
import sys
import tempfile
import time
import urlparse

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.timezone import now
from django.test.utils import override_settings

# AWX
from awx.main.licenses import LicenseWriter
from awx.main.models import *
from awx.main.tests.base import BaseTest, BaseLiveServerTest

__all__ = ['DumpDataTest', 'CleanupDeletedTest', 'CleanupJobsTest',
           'InventoryImportTest']

TEST_PLAYBOOK = '''- hosts: test-group
  gather_facts: False
  tasks:
  - name: should pass
    command: test 1 = 1
  - name: should also pass
    command: test 2 = 2
'''

TEST_INVENTORY_INI = '''\
# Some comment about blah blah blah...

[webservers]
web1.example.com ansible_ssh_host=w1.example.net
web2.example.com
web3.example.com:1022

[webservers:vars]   # Comment on a section
webvar=blah         # Comment on an option

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

TEST_INVENTORY_INI_WITH_HOST_PATTERNS = '''\
[dotcom]
web[00:63].example.com ansible_ssh_user=example
dns.example.com

[dotnet]
db-[a:z].example.net
ns.example.net

[dotorg]
[A:F][0:9].example.org:1022 ansible_ssh_user=example
mx.example.org

[dotus]
lb[00:08:2].example.us even_odd=even
lb[01:09:2].example.us even_odd=odd

[dotcc]
media[0:9][0:9].example.cc
'''

TEST_GROUP_VARS = '''\
test_username: test
test_email: test@example.com
'''

class BaseCommandMixin(object):
    '''
    Base class for tests that run management commands.
    '''

    def setUp(self):
        super(BaseCommandMixin, self).setUp()
        self._sys_path = [x for x in sys.path]
        self._environ = dict(os.environ.items())
        self._temp_files = []

    def tearDown(self):
        super(BaseCommandMixin, self).tearDown()
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

class DumpDataTest(BaseCommandMixin, BaseTest):
    '''
    Test cases for dumpdata management command.
    '''

    def setUp(self):
        super(DumpDataTest, self).setUp()
        self.create_test_inventories()

    def test_dumpdata(self):
        result, stdout, stderr = self.run_command('dumpdata')
        self.assertEqual(result, None)
        data = json.loads(stdout)

class CleanupDeletedTest(BaseCommandMixin, BaseTest):
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
            self.assertTrue(len(user.username) <= 30,
                            'len(%r) == %d' % (user.username, len(user.username)))
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

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   ANSIBLE_TRANSPORT='local')
class CleanupJobsTest(BaseCommandMixin, BaseLiveServerTest):
    '''
    Test cases for cleanup_jobs management command.
    '''

    def setUp(self):
        super(CleanupJobsTest, self).setUp()
        self.test_project_path = None
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.inventory = Inventory.objects.create(name='test-inventory',
                                                  description='description for test-inventory',
                                                  organization=self.organization)
        self.host = self.inventory.hosts.create(name='host.example.com',
                                                inventory=self.inventory)
        self.group = self.inventory.groups.create(name='test-group',
                                                  inventory=self.inventory)
        self.group.hosts.add(self.host)
        self.project = None
        self.credential = None
        settings.INTERNAL_API_URL = self.live_server_url
        self.start_taskmanager(settings.TASK_COMMAND_PORT)
        self.start_queue(settings.CALLBACK_CONSUMER_PORT, settings.CALLBACK_QUEUE_PORT)

    def tearDown(self):
        super(CleanupJobsTest, self).tearDown()
        self.terminate_queue()
        self.terminate_taskmanager()
        if self.test_project_path:
            shutil.rmtree(self.test_project_path, True)

    def create_test_credential(self, **kwargs):
        opts = {
            'name': 'test-creds',
            'user': self.super_django_user,
            'ssh_username': '',
            'ssh_key_data': '',
            'ssh_key_unlock': '',
            'ssh_password': '',
            'sudo_username': '',
            'sudo_password': '',
        }
        opts.update(kwargs)
        self.credential = Credential.objects.create(**opts)
        return self.credential

    def create_test_project(self, playbook_content):
        self.project = self.make_projects(self.normal_django_user, 1, playbook_content)[0]
        self.organization.projects.add(self.project)

    def create_test_job_template(self, **kwargs):
        opts = {
            'name': 'test-job-template %s' % str(now()),
            'inventory': self.inventory,
            'project': self.project,
            'credential': self.credential,
            'job_type': 'run',
        }
        try:
            opts['playbook'] = self.project.playbooks[0]
        except (AttributeError, IndexError):
            pass
        opts.update(kwargs)
        self.job_template = JobTemplate.objects.create(**opts)
        return self.job_template

    def create_test_job(self, **kwargs):
        job_template = kwargs.pop('job_template', None)
        if job_template:
            self.job = job_template.create_job(**kwargs)
        else:
            opts = {
                'name': 'test-job %s' % str(now()),
                'inventory': self.inventory,
                'project': self.project,
                'credential': self.credential,
                'job_type': 'run',
            }
            try:
                opts['playbook'] = self.project.playbooks[0]
            except (AttributeError, IndexError):
                pass
            opts.update(kwargs)
            self.job = Job.objects.create(**opts)
        return self.job

    def test_cleanup_jobs(self):
        # Test with no jobs to be cleaned up.
        jobs_before = Job.objects.all().count()
        self.assertFalse(jobs_before)
        result, stdout, stderr = self.run_command('cleanup_jobs')
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertEqual(jobs_before, jobs_after)        
        # Create and run job.
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        self.assertEqual(job.status, 'waiting')
        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, 'successful')
        # With days=1, no jobs will be deleted.
        jobs_before = Job.objects.all().count()
        self.assertTrue(jobs_before)
        result, stdout, stderr = self.run_command('cleanup_jobs', days=1)
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertEqual(jobs_before, jobs_after)
        # With days=0 and dry_run=True, no jobs will be deleted.
        jobs_before = Job.objects.all().count()
        self.assertTrue(jobs_before)
        result, stdout, stderr = self.run_command('cleanup_jobs', days=0,
                                                  dry_run=True)
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertEqual(jobs_before, jobs_after)
        # With days=0, our job will be deleted.
        jobs_before = Job.objects.all().count()
        self.assertTrue(jobs_before)
        result, stdout, stderr = self.run_command('cleanup_jobs', days=0)
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertNotEqual(jobs_before, jobs_after)
        self.assertFalse(jobs_after)

class InventoryImportTest(BaseCommandMixin, BaseLiveServerTest):
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

    def create_test_ini(self, inv_dir=None, ini_content=None):
        ini_content = ini_content or TEST_INVENTORY_INI
        handle, self.ini_path = tempfile.mkstemp(suffix='.txt', dir=inv_dir)
        ini_file = os.fdopen(handle, 'w')
        ini_file.write(ini_content)
        ini_file.close()
        self._temp_files.append(self.ini_path)

    def create_test_dir(self, hostnames=None):
        hostnames = hostnames or []
        self.inv_dir = tempfile.mkdtemp()
        self._temp_project_dirs.append(self.inv_dir)
        self.create_test_ini(self.inv_dir)
        group_vars = os.path.join(self.inv_dir, 'group_vars')
        os.makedirs(group_vars)
        file(os.path.join(group_vars, 'all'), 'wb').write(TEST_GROUP_VARS)
        if hostnames:
            host_vars = os.path.join(self.inv_dir, 'host_vars')
            os.makedirs(host_vars)
            for hostname in hostnames:
                test_host_vars = '''test_hostname: %s''' % hostname
                file(os.path.join(host_vars, hostname), 'wb').write(test_host_vars)

    def check_adhoc_inventory_source(self, inventory, except_host_pks=None,
                                     except_group_pks=None):
        # Check that management command created a new inventory source and
        # related inventory update.
        inventory_sources = inventory.inventory_sources.filter(group=None)
        self.assertEqual(inventory_sources.count(), 1)
        inventory_source = inventory_sources[0]
        self.assertEqual(inventory_source.source, 'file')
        self.assertEqual(inventory_source.inventory_updates.count(), 1)
        inventory_update = inventory_source.inventory_updates.all()[0]
        self.assertEqual(inventory_update.status, 'successful')
        for host in inventory.hosts.filter(active=True):
            if host.pk in (except_host_pks or []):
                continue
            source_pks = host.inventory_sources.values_list('pk', flat=True)
            self.assertTrue(inventory_source.pk in source_pks)
        for group in inventory.groups.filter(active=True):
            if group.pk in (except_group_pks or []):
                continue
            source_pks = group.inventory_sources.values_list('pk', flat=True)
            self.assertTrue(inventory_source.pk in source_pks)

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
        self.assertTrue(isinstance(result, IOError), result)
        self.assertTrue('not exist' in str(result))
        # Invalid inventory ID.
        invalid_id = Inventory.objects.order_by('-pk')[0].pk + 1
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=invalid_id,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('found' in str(result))
        # Invalid inventory name.
        invalid_name = 'invalid inventory name'
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_name=invalid_name,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, CommandError), result)
        self.assertTrue('found' in str(result))

    def test_ini_file(self, source=None):
        inv_src = source or self.ini_path
        # New empty inventory.
        new_inv = self.organizations[0].inventories.create(name='newb')
        self.assertEqual(new_inv.hosts.count(), 0)
        self.assertEqual(new_inv.groups.count(), 0)
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=inv_src)
        self.assertEqual(result, None)
        # Check that inventory is populated as expected.
        new_inv = Inventory.objects.get(pk=new_inv.pk)
        expected_group_names = set(['servers', 'dbservers', 'webservers'])
        group_names = set(new_inv.groups.values_list('name', flat=True))
        self.assertEqual(expected_group_names, group_names)
        expected_host_names = set(['web1.example.com', 'web2.example.com',
                                   'web3.example.com', 'db1.example.com',
                                   'db2.example.com'])
        host_names = set(new_inv.hosts.values_list('name', flat=True))
        self.assertEqual(expected_host_names, host_names)
        if source:
            self.assertEqual(new_inv.variables_dict, {
                'vara': 'A',
                'test_username': 'test',
                'test_email': 'test@example.com',
            })
        else:
            self.assertEqual(new_inv.variables_dict, {'vara': 'A'})
        for host in new_inv.hosts.all():
            if host.name == 'web1.example.com':
                self.assertEqual(host.variables_dict,
                                {'ansible_ssh_host': 'w1.example.net'})
            elif host.name in ('db1.example.com', 'db2.example.com') and source and os.path.isdir(source):
                self.assertEqual(host.variables_dict, {'test_hostname': host.name})
            elif host.name == 'web3.example.com':
                self.assertEqual(host.variables_dict, {'ansible_ssh_port': 1022})
            else:
                self.assertEqual(host.variables_dict, {})
        for group in new_inv.groups.all():
            if group.name == 'servers':
                self.assertEqual(group.variables_dict, {'varb': 'B'})
                children = set(group.children.values_list('name', flat=True))
                self.assertEqual(children, set(['dbservers', 'webservers']))
                self.assertEqual(group.hosts.count(), 0)
            elif group.name == 'dbservers':
                self.assertEqual(group.variables_dict, {'dbvar': 'ugh'})
                self.assertEqual(group.children.count(), 0)
                hosts = set(group.hosts.values_list('name', flat=True))
                host_names = set(['db1.example.com','db2.example.com'])
                self.assertEqual(hosts, host_names)                
            elif group.name == 'webservers':
                self.assertEqual(group.variables_dict, {'webvar': 'blah'})
                self.assertEqual(group.children.count(), 0)
                hosts = set(group.hosts.values_list('name', flat=True))
                host_names = set(['web1.example.com','web2.example.com',
                                  'web3.example.com'])
                self.assertEqual(hosts, host_names)
        self.check_adhoc_inventory_source(new_inv)

    def test_dir_with_ini_file(self):
        self.create_test_dir(hostnames=['db1.example.com', 'db2.example.com'])
        self.test_ini_file(self.inv_dir)

    def test_merge_from_ini_file(self, overwrite=False, overwrite_vars=False):
        new_inv_vars = json.dumps({'varc': 'C'})
        new_inv = self.organizations[0].inventories.create(name='inv123',
                                                           variables=new_inv_vars)
        lb_host_vars = json.dumps({'lbvar': 'ni!'})
        lb_host = new_inv.hosts.create(name='lb.example.com',
                                       variables=lb_host_vars)
        lb_group = new_inv.groups.create(name='lbservers')
        servers_group_vars = json.dumps({'vard': 'D'})
        servers_group = new_inv.groups.create(name='servers',
                                              variables=servers_group_vars)
        servers_group.children.add(lb_group)
        lb_group.hosts.add(lb_host)
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path,
                                                  overwrite=overwrite,
                                                  overwrite_vars=overwrite_vars)
        self.assertEqual(result, None)
        # Check that inventory is populated as expected.
        new_inv = Inventory.objects.get(pk=new_inv.pk)
        expected_group_names = set(['servers', 'dbservers', 'webservers',
                                    'lbservers'])
        if overwrite:
            expected_group_names.remove('lbservers')
        group_names = set(new_inv.groups.filter(active=True).values_list('name', flat=True))
        self.assertEqual(expected_group_names, group_names)
        expected_host_names = set(['web1.example.com', 'web2.example.com',
                                   'web3.example.com', 'db1.example.com',
                                   'db2.example.com', 'lb.example.com'])
        if overwrite:
            expected_host_names.remove('lb.example.com')
        host_names = set(new_inv.hosts.filter(active=True).values_list('name', flat=True))
        self.assertEqual(expected_host_names, host_names)
        expected_inv_vars = {'vara': 'A', 'varc': 'C'}
        if overwrite or overwrite_vars:
            expected_inv_vars.pop('varc')
        self.assertEqual(new_inv.variables_dict, expected_inv_vars)
        for host in new_inv.hosts.filter(active=True):
            if host.name == 'web1.example.com':
                self.assertEqual(host.variables_dict,
                                {'ansible_ssh_host': 'w1.example.net'})
            elif host.name == 'web3.example.com':
                self.assertEqual(host.variables_dict, {'ansible_ssh_port': 1022})
            elif host.name == 'lb.example.com':
                self.assertEqual(host.variables_dict, {'lbvar': 'ni!'})
            else:
                self.assertEqual(host.variables_dict, {})
        for group in new_inv.groups.filter(active=True):
            if group.name == 'servers':
                expected_vars = {'varb': 'B', 'vard': 'D'}
                if overwrite or overwrite_vars:
                    expected_vars.pop('vard')
                self.assertEqual(group.variables_dict, expected_vars)
                children = set(group.children.filter(active=True).values_list('name', flat=True))
                expected_children = set(['dbservers', 'webservers', 'lbservers'])
                if overwrite:
                    expected_children.remove('lbservers')
                self.assertEqual(children, expected_children)
                self.assertEqual(group.hosts.filter(active=True).count(), 0)
            elif group.name == 'dbservers':
                self.assertEqual(group.variables_dict, {'dbvar': 'ugh'})
                self.assertEqual(group.children.filter(active=True).count(), 0)
                hosts = set(group.hosts.filter(active=True).values_list('name', flat=True))
                host_names = set(['db1.example.com','db2.example.com'])
                self.assertEqual(hosts, host_names)                
            elif group.name == 'webservers':
                self.assertEqual(group.variables_dict, {'webvar': 'blah'})
                self.assertEqual(group.children.filter(active=True).count(), 0)
                hosts = set(group.hosts.filter(active=True).values_list('name', flat=True))
                host_names = set(['web1.example.com','web2.example.com',
                                  'web3.example.com'])
                self.assertEqual(hosts, host_names)
            elif group.name == 'lbservers':
                self.assertEqual(group.variables_dict, {})
                self.assertEqual(group.children.filter(active=True).count(), 0)
                hosts = set(group.hosts.filter(active=True).values_list('name', flat=True))
                host_names = set(['lb.example.com'])
                self.assertEqual(hosts, host_names)
        if overwrite:
            except_host_pks = set()
            except_group_pks = set()
        else:
            except_host_pks = set([lb_host.pk])
            except_group_pks = set([lb_group.pk])
        self.check_adhoc_inventory_source(new_inv, except_host_pks,
                                          except_group_pks)

    def test_overwrite_vars_from_ini_file(self):
        self.test_merge_from_ini_file(overwrite_vars=True)

    def test_overwrite_from_ini_file(self):
        self.test_merge_from_ini_file(overwrite=True)

    def test_ini_file_with_host_patterns(self):
        self.create_test_ini(ini_content=TEST_INVENTORY_INI_WITH_HOST_PATTERNS)
        # New empty inventory.
        new_inv = self.organizations[0].inventories.create(name='newb')
        self.assertEqual(new_inv.hosts.count(), 0)
        self.assertEqual(new_inv.groups.count(), 0)
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertEqual(result, None, stdout + stderr)
        # Check that inventory is populated as expected.
        new_inv = Inventory.objects.get(pk=new_inv.pk)
        expected_group_names = set(['dotcom', 'dotnet', 'dotorg', 'dotus', 'dotcc'])
        group_names = set(new_inv.groups.values_list('name', flat=True))
        self.assertEqual(expected_group_names, group_names)
        # Check that all host ranges are expanded into host names.
        expected_host_names = set()
        expected_host_names.update(['web%02d.example.com' % x for x in xrange(64)])
        expected_host_names.add('dns.example.com')
        expected_host_names.update(['db-%s.example.net' % x for x in string.ascii_lowercase])
        expected_host_names.add('ns.example.net')
        for x in 'ABCDEF':
            for y in xrange(10):
                expected_host_names.add('%s%d.example.org' % (x, y))
        expected_host_names.add('mx.example.org')
        expected_host_names.update(['lb%02d.example.us' % x for x in xrange(10)])
        expected_host_names.update(['media%02d.example.cc' % x for x in xrange(100)])
        host_names = set(new_inv.hosts.values_list('name', flat=True))
        self.assertEqual(expected_host_names, host_names)
        # Check hosts in dotcom group.
        group = new_inv.groups.get(name='dotcom')
        self.assertEqual(group.hosts.count(), 65)
        for host in group.hosts.filter(active=True, name__startswith='web'):
            self.assertEqual(host.variables_dict.get('ansible_ssh_user', ''), 'example')
        # Check hosts in dotnet group.
        group = new_inv.groups.get(name='dotnet')
        self.assertEqual(group.hosts.count(), 27)
        # Check hosts in dotorg group.
        group = new_inv.groups.get(name='dotorg')
        self.assertEqual(group.hosts.count(), 61)
        for host in group.hosts.filter(active=True):
            if host.name.startswith('mx.'):
                continue
            self.assertEqual(host.variables_dict.get('ansible_ssh_user', ''), 'example')
            self.assertEqual(host.variables_dict.get('ansible_ssh_port', 22), 1022)
        # Check hosts in dotus group.
        group = new_inv.groups.get(name='dotus')
        self.assertEqual(group.hosts.count(), 10)
        for host in group.hosts.filter(active=True):
            if int(host.name[2:4]) % 2 == 0:
                self.assertEqual(host.variables_dict.get('even_odd', ''), 'even')
            else:
                self.assertEqual(host.variables_dict.get('even_odd', ''), 'odd')
        # Check hosts in dotcc group.
        group = new_inv.groups.get(name='dotcc')
        self.assertEqual(group.hosts.count(), 100)
        # Check inventory source/update after running command.
        self.check_adhoc_inventory_source(new_inv)
        # Test with invalid host pattern -- alpha begin > end.
        self.create_test_ini(ini_content='[invalid]\nhost[X:P]')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, ValueError), result)
        # Test with invalid host pattern -- different numeric pattern lengths.
        self.create_test_ini(ini_content='[invalid]\nhost[001:08]')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, ValueError), result)
        # Test with invalid host pattern -- invalid range/slice spec.
        self.create_test_ini(ini_content='[invalid]\nhost[1:2:3:4]')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, ValueError), result)
        # Test with invalid host pattern -- no begin.
        self.create_test_ini(ini_content='[invalid]\nhost[:9]')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, ValueError), result)
        # Test with invalid host pattern -- no end.
        self.create_test_ini(ini_content='[invalid]\nhost[0:]')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, ValueError), result)
        # Test with invalid host pattern -- invalid slice.
        self.create_test_ini(ini_content='[invalid]\nhost[0:9:Q]')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=self.ini_path)
        self.assertTrue(isinstance(result, ValueError), result)

    def test_executable_file(self):
        # New empty inventory.
        old_inv = self.inventories[1]
        new_inv = self.organizations[0].inventories.create(name='newb')
        self.assertEqual(new_inv.hosts.count(), 0)
        self.assertEqual(new_inv.groups.count(), 0)
        # Use our own inventory script as executable file.
        rest_api_url = self.live_server_url
        parts = urlparse.urlsplit(rest_api_url)
        username, password = self.get_super_credentials()
        netloc = '%s:%s@%s' % (username, password, parts.netloc)
        rest_api_url = urlparse.urlunsplit([parts.scheme, netloc, parts.path,
                                            parts.query, parts.fragment])
        os.environ.setdefault('REST_API_URL', rest_api_url)
        os.environ['INVENTORY_ID'] = str(old_inv.pk)        
        source = os.path.join(os.path.dirname(__file__), '..', '..', 'plugins',
                              'inventory', 'awxrest.py')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=source)
        self.assertEqual(result, None)
        # Check that inventory is populated as expected.
        new_inv = Inventory.objects.get(pk=new_inv.pk)
        self.assertEqual(old_inv.variables_dict, new_inv.variables_dict)
        old_groups = set(old_inv.groups.values_list('name', flat=True))
        new_groups = set(new_inv.groups.values_list('name', flat=True))
        self.assertEqual(old_groups, new_groups)
        old_hosts = set(old_inv.hosts.values_list('name', flat=True))
        new_hosts = set(new_inv.hosts.values_list('name', flat=True))
        self.assertEqual(old_hosts, new_hosts)
        for new_host in new_inv.hosts.all():
            old_host = old_inv.hosts.get(name=new_host.name)
            self.assertEqual(old_host.variables_dict, new_host.variables_dict)
        for new_group in new_inv.groups.all():
            old_group = old_inv.groups.get(name=new_group.name)
            self.assertEqual(old_group.variables_dict, new_group.variables_dict)
            old_children = set(old_group.children.values_list('name', flat=True))
            new_children = set(new_group.children.values_list('name', flat=True))
            self.assertEqual(old_children, new_children)
            old_hosts = set(old_group.hosts.values_list('name', flat=True))
            new_hosts = set(new_group.hosts.values_list('name', flat=True))
            self.assertEqual(old_hosts, new_hosts)
        self.check_adhoc_inventory_source(new_inv)

    def test_executable_file_with_meta_hostvars(self):
        os.environ['INVENTORY_HOSTVARS'] = '1'
        self.test_executable_file()

    def test_large_executable_file(self):
        new_inv = self.organizations[0].inventories.create(name='newec2')
        self.assertEqual(new_inv.hosts.count(), 0)
        self.assertEqual(new_inv.groups.count(), 0)
        inv_file = os.path.join(os.path.dirname(__file__), 'data',
                                'large_ec2_inventory.py')
        result, stdout, stderr = self.run_command('inventory_import',
                                                  inventory_id=new_inv.pk,
                                                  source=inv_file)
        self.assertEqual(result, None)
        # Check that inventory is populated as expected within a reasonable
        # amount of time.  Computed fields should also be updated.
        new_inv = Inventory.objects.get(pk=new_inv.pk)
        self.assertNotEqual(new_inv.hosts.count(), 0)
        self.assertNotEqual(new_inv.groups.count(), 0)
        self.assertNotEqual(new_inv.total_hosts, 0)
        self.assertNotEqual(new_inv.total_groups, 0)
        self.assertElapsedLessThan(60)

