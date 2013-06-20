# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import json
import os
import StringIO
import sys
import tempfile
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.timezone import now
from ansibleworks.main.models import *
from ansibleworks.main.tests.base import BaseTest

__all__ = ['RunCommandAsScriptTest',# 'AcomInventoryTest',
           'AcomCallbackEventTest']

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
        return result, captured_stdout, captured_stderr

class RunCommandAsScriptTest(BaseCommandTest):
    '''
    Test helper to run management command as standalone script.
    '''

    def test_run_command_as_script(self):
        from ansibleworks.main.management.commands import run_command_as_script
        os.environ['ACOM_TEST_DATABASE_NAME'] = settings.DATABASES['default']['NAME']
        # FIXME: Not sure how to test ImportError for settings module.
        def run_cmd(name, *args, **kwargs):
            return run_command_as_script(name)
        result, stdout, stderr = self.run_command('version',
                                                  command_runner=run_cmd)
        self.assertEqual(result, None)
        self.assertTrue(stdout)
        self.assertFalse(stderr)

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
                if x in (3, 7):
                    host.mark_inactive()
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
                if x == 2:
                    group.mark_inactive()
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
        self.assertTrue(inventory.active)
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  inventory_id=inventory.pk)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        groups = inventory.groups.filter(active=True)
        groupnames = groups.values_list('name', flat=True)
        self.assertEqual(set(data.keys()), set(groupnames))
        # Groups for this inventory should only have hosts, and no group
        # variable data or parent/child relationships.
        for k,v in data.items():
            self.assertTrue(isinstance(v, (list, tuple)))
            group = inventory.groups.get(active=True, name=k)
            hosts = group.hosts.filter(active=True)
            hostnames = hosts.values_list('name', flat=True)
            self.assertEqual(set(v), set(hostnames))
        for group in inventory.groups.filter(active=False):
            self.assertFalse(group.name in data.keys(),
                             'deleted group %s should not be in data' % group)
        # Command line argument for inventory ID should take precedence over
        # environment variable.
        inventory_pks = set(map(lambda x: x.pk, self.inventories))
        invalid_id = [x for x in xrange(9999) if x not in inventory_pks][0]
        os.environ['ACOM_INVENTORY_ID'] = str(invalid_id)
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  inventory_id=inventory.pk)
        self.assertEqual(result, None)
        data = json.loads(stdout)

    def test_list_with_inventory_id_in_environment(self):
        inventory = self.inventories[1]
        self.assertTrue(inventory.active)
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        groups = inventory.groups.filter(active=True)
        groupnames = list(groups.values_list('name', flat=True)) + ['all']
        self.assertEqual(set(data.keys()), set(groupnames))
        # Groups for this inventory should have hosts, variable data, and one
        # parent/child relationship.
        for k,v in data.items():
            self.assertTrue(isinstance(v, dict))
            if k == 'all':
                self.assertEqual(v.get('vars', {}), inventory.variables_dict)
                continue
            group = inventory.groups.get(active=True, name=k)
            hosts = group.hosts.filter(active=True)
            hostnames = hosts.values_list('name', flat=True)
            self.assertEqual(set(v.get('hosts', [])), set(hostnames))
            if group.variables:
                self.assertEqual(v.get('vars', {}),
                                 json.loads(group.variables))
            if k == 'group-3':
                children = group.children.filter(active=True)
                childnames = children.values_list('name', flat=True)
                self.assertEqual(set(v.get('children', [])), set(childnames))
            else:
                self.assertFalse('children' in v)

    def test_valid_host(self):
        # Host without variable data.
        inventory = self.inventories[0]
        self.assertTrue(inventory.active)
        host = inventory.hosts.filter(active=True)[2]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=host.name)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(data, {})
        # Host with variable data.
        inventory = self.inventories[1]
        self.assertTrue(inventory.active)
        host = inventory.hosts.filter(active=True)[4]
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory',
                                                  host=host.name)
        self.assertEqual(result, None)
        data = json.loads(stdout)
        self.assertEqual(data, json.loads(host.variables))

    def test_invalid_host(self):
        # Valid host, but not part of the specified inventory.
        inventory = self.inventories[0]
        self.assertTrue(inventory.active)
        host = Host.objects.exclude(inventory=inventory)[0]
        self.assertTrue(host.active)
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
        invalid_id = [x for x in xrange(1, 9999) if x not in inventory_pks][0]
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

    def test_with_deleted_inventory(self):
        inventory = self.inventories[0]
        inventory.mark_inactive()
        self.assertFalse(inventory.active)
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_without_list_or_host_argument(self):
        inventory = self.inventories[0]
        self.assertTrue(inventory.active)
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory')
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_with_both_list_and_host_arguments(self):
        inventory = self.inventories[0]
        self.assertTrue(inventory.active)
        os.environ['ACOM_INVENTORY_ID'] = str(inventory.pk)
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  host='blah')
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

class AcomCallbackEventTest(BaseCommandTest):
    '''
    Test cases for acom_callback_event management command.
    '''

    def setUp(self):
        super(AcomCallbackEventTest, self).setUp()
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.project = self.make_projects(self.normal_django_user, 1)[0]
        self.organization.projects.add(self.project)
        self.inventory = Inventory.objects.create(name='test-inventory',
                                                  organization=self.organization)
        self.host = self.inventory.hosts.create(name='host.example.com',
                                                inventory=self.inventory)
        self.group = self.inventory.groups.create(name='test-group',
                                                  inventory=self.inventory)
        self.group.hosts.add(self.host)
        self.job = Job.objects.create(name='job-%s' % now().isoformat(),
                                      inventory=self.inventory,
                                      project=self.project)
        self.valid_kwargs = {
            'job_id': self.job.id,
            'event_type': 'playbook_on_start',
            'event_data_json': json.dumps({'test_event_data': [2,4,6]}),
        }

    def test_with_job_status_not_running(self):
        # Events can only be added when the job is running.
        self.assertEqual(self.job.status, 'new')
        self.job.status = 'pending'
        self.job.save()
        result, stdout, stderr = self.run_command('acom_callback_event',
                                                  **self.valid_kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('unable to add event ' in str(result).lower())
        self.job.status = 'successful'
        self.job.save()
        result, stdout, stderr = self.run_command('acom_callback_event',
                                                  **self.valid_kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('unable to add event ' in str(result).lower())
        self.job.status = 'failed'
        self.job.save()
        result, stdout, stderr = self.run_command('acom_callback_event',
                                                  **self.valid_kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('unable to add event ' in str(result).lower())

    def test_with_invalid_args(self):
        self.job.status = 'running'
        self.job.save()
        # Event type not given.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('event_type')
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('no event specified' in str(result).lower())
        # Invalid event type.
        kwargs = dict(self.valid_kwargs.items())
        kwargs['event_type'] = 'invalid_event_type'
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('unsupported event' in str(result).lower())
        # Neither file or data specified.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('event_data_json')
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('either --file or --data' in str(result).lower())
        # Non-integer job ID.
        kwargs = dict(self.valid_kwargs.items())
        kwargs['job_id'] = 'foo'
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('id must be an integer' in str(result).lower())
        # No job ID.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('job_id')
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('no job id' in str(result).lower())
        # Invalid job ID.
        kwargs = dict(self.valid_kwargs.items())
        kwargs['job_id'] = 9999
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('not found' in str(result).lower())
        # Invalid inline JSON data.
        kwargs = dict(self.valid_kwargs.items())
        kwargs['event_data_json'] = 'invalid json'
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('error parsing json' in str(result).lower())
        # Invalid file specified.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('event_data_json')
        h, tf = tempfile.mkstemp()
        os.close(h)
        os.remove(tf)
        kwargs['event_data_file'] = '%s.json' % tf
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertTrue(isinstance(result, CommandError))
        self.assertTrue('reading from' in str(result).lower())

    def test_with_valid_args(self):
        self.job.status = 'running'
        self.job.save()
        # Default valid args.
        kwargs = dict(self.valid_kwargs.items())
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertEqual(result, None)
        self.assertEqual(self.job.job_events.count(), 1)
        # Pass job ID in environment instead.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('job_id')
        os.environ['ACOM_JOB_ID'] = str(self.job.id)
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertEqual(result, None)
        self.assertEqual(self.job.job_events.count(), 2)
        os.environ.pop('ACOM_JOB_ID', None)
        # Test with JSON data in a file instead.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('event_data_json')
        h, tf = tempfile.mkstemp(suffix='.json')
        self._temp_files.append(tf)
        f = os.fdopen(h, 'w')
        json.dump({'some_event_data': [1, 2, 3]}, f)
        f.close()
        kwargs['event_data_file'] = tf
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertEqual(result, None)
        self.assertEqual(self.job.job_events.count(), 3)
        # Test with JSON data from stdin.
        kwargs = dict(self.valid_kwargs.items())
        kwargs.pop('event_data_json')
        kwargs['event_data_file'] = '-'
        kwargs['stdin_fileobj'] = StringIO.StringIO(json.dumps({'blah': 'bleep'}))
        result, stdout, stderr = self.run_command('acom_callback_event', **kwargs)
        self.assertEqual(result, None)
        self.assertEqual(self.job.job_events.count(), 4)
