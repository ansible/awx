# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import json
import os
import shutil
import StringIO
import sys
import time
import unittest2 as unittest

# Django
from django.core.management import call_command
from django.utils.timezone import now
from django.test.utils import override_settings

# AWX
from awx.main.models import * # noqa
from awx.main.tests.base import BaseTest, BaseLiveServerTest

__all__ = ['CreateDefaultOrgTest', 'DumpDataTest', 'CleanupDeletedTest',
           'CleanupJobsTest', 'CleanupActivityStreamTest',
           'InventoryImportTest']

TEST_PLAYBOOK = '''- hosts: test-group
  gather_facts: False
  tasks:
  - name: should pass
    command: test 1 = 1
  - name: should also pass
    command: test 2 = 2
'''


class BaseCommandMixin(object):
    '''
    Base class for tests that run management commands.
    '''

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
        except Exception as e:
            result = e
        finally:
            captured_stdout = sys.stdout.getvalue()
            captured_stderr = sys.stderr.getvalue()
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        return result, captured_stdout, captured_stderr


class CreateDefaultOrgTest(BaseCommandMixin, BaseTest):
    '''
    Test cases for create_default_org management command.
    '''

    def setUp(self):
        super(CreateDefaultOrgTest, self).setUp()
        self.setup_instances()

    def test_create_default_org(self):
        self.setup_users()
        self.assertEqual(Organization.objects.count(), 0)
        result, stdout, stderr = self.run_command('create_preload_data')
        self.assertEqual(result, None)
        self.assertTrue('Default organization added' in stdout)
        self.assertEqual(Organization.objects.count(), 1)
        org = Organization.objects.all()[0]
        self.assertEqual(org.created_by, self.super_django_user)
        self.assertEqual(org.modified_by, self.super_django_user)
        result, stdout, stderr = self.run_command('create_preload_data')
        self.assertEqual(result, None)
        self.assertFalse('Default organization added' in stdout)
        self.assertEqual(Organization.objects.count(), 1)


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
        json.loads(stdout)


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
        self.setup_instances()
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
        self.start_queue()

    def tearDown(self):
        super(CleanupJobsTest, self).tearDown()
        self.terminate_queue()
        if self.test_project_path:
            shutil.rmtree(self.test_project_path, True)

    def create_test_credential(self, **kwargs):
        self.credential = self.make_credential(**kwargs)
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

    def create_test_ad_hoc_command(self, **kwargs):
        opts = {
            'inventory': self.inventory,
            'credential': self.credential,
            'module_name': 'command',
            'module_args': 'uptime',
        }
        opts.update(kwargs)
        self.ad_hoc_command = AdHocCommand.objects.create(**opts)
        return self.ad_hoc_command

    def test_cleanup_jobs(self):
        # Test with no jobs to be cleaned up.
        jobs_before = Job.objects.all().count()
        self.assertFalse(jobs_before)
        ad_hoc_commands_before = AdHocCommand.objects.all().count()
        self.assertFalse(ad_hoc_commands_before)
        result, stdout, stderr = self.run_command('cleanup_jobs')
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertEqual(jobs_before, jobs_after)
        ad_hoc_commands_after = AdHocCommand.objects.all().count()
        self.assertEqual(ad_hoc_commands_before, ad_hoc_commands_after)

        # Create and run job.
        self.create_test_credential()
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, 'successful')

        # Create and run ad hoc command.
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.assertEqual(ad_hoc_command.status, 'successful')

        # With days=1, no jobs will be deleted.
        jobs_before = Job.objects.all().count()
        self.assertTrue(jobs_before)
        ad_hoc_commands_before = AdHocCommand.objects.all().count()
        self.assertTrue(ad_hoc_commands_before)
        result, stdout, stderr = self.run_command('cleanup_jobs', days=1)
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertEqual(jobs_before, jobs_after)
        ad_hoc_commands_after = AdHocCommand.objects.all().count()
        self.assertEqual(ad_hoc_commands_before, ad_hoc_commands_after)

        # With days=0 and dry_run=True, no jobs will be deleted.
        jobs_before = Job.objects.all().count()
        self.assertTrue(jobs_before)
        ad_hoc_commands_before = AdHocCommand.objects.all().count()
        self.assertTrue(ad_hoc_commands_before)
        result, stdout, stderr = self.run_command('cleanup_jobs', days=0,
                                                  dry_run=True)
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertEqual(jobs_before, jobs_after)
        ad_hoc_commands_after = AdHocCommand.objects.all().count()
        self.assertEqual(ad_hoc_commands_before, ad_hoc_commands_after)

        # With days=0, our job and ad hoc command will be deleted.
        jobs_before = Job.objects.all().count()
        self.assertTrue(jobs_before)
        ad_hoc_commands_before = AdHocCommand.objects.all().count()
        self.assertTrue(ad_hoc_commands_before)
        result, stdout, stderr = self.run_command('cleanup_jobs', days=0)
        self.assertEqual(result, None)
        jobs_after = Job.objects.all().count()
        self.assertNotEqual(jobs_before, jobs_after)
        self.assertFalse(jobs_after)
        ad_hoc_commands_after = AdHocCommand.objects.all().count()
        self.assertNotEqual(ad_hoc_commands_before, ad_hoc_commands_after)
        self.assertFalse(ad_hoc_commands_after)


@unittest.skipIf(os.environ.get('SKIP_SLOW_TESTS', False), 'Skipping slow test')
class CleanupActivityStreamTest(BaseCommandMixin, BaseTest):
    '''
    Test cases for cleanup_activitystream management command.
    '''

    def setUp(self):
        super(CleanupActivityStreamTest, self).setUp()
        self.start_rabbit()
        self.create_test_inventories()

    def tearDown(self):
        self.stop_rabbit()
        super(CleanupActivityStreamTest, self).tearDown()

    def test_cleanup(self):
        # Should already have entries due to test case setup. With no
        # parameters, "days" defaults to 30, which won't cleanup anything.
        count_before = ActivityStream.objects.count()
        self.assertTrue(count_before)
        result, stdout, stderr = self.run_command('cleanup_activitystream')
        self.assertEqual(result, None)
        count_after = ActivityStream.objects.count()
        self.assertEqual(count_before, count_after)

        # With days=1, nothing should be changed.
        result, stdout, stderr = self.run_command('cleanup_activitystream', days=1)
        self.assertEqual(result, None)
        count_after = ActivityStream.objects.count()
        self.assertEqual(count_before, count_after)

        # With days=0 and dry_run=True, nothing should be changed.
        result, stdout, stderr = self.run_command('cleanup_activitystream', days=0, dry_run=True)
        self.assertEqual(result, None)
        count_after = ActivityStream.objects.count()
        self.assertEqual(count_before, count_after)

        # With days=0, everything should be cleaned up.
        result, stdout, stderr = self.run_command('cleanup_activitystream', days=0)
        self.assertEqual(result, None)
        count_after = ActivityStream.objects.count()
        self.assertNotEqual(count_before, count_after)
        self.assertFalse(count_after)

        # Modify hosts to create 1000 activity stream entries.
        t = time.time()
        for x in xrange(0, 1000 / Host.objects.count()):
            for host in Host.objects.all():
                host.name = u'%s-update-%d' % (host.name, x)
                host.save()
        create_elapsed = time.time() - t

        # Time how long it takes to cleanup activity stream, should be no more
        # than 1/4 the time taken to create the entries.
        count_before = ActivityStream.objects.count()
        self.assertTrue(count_before)
        t = time.time()
        result, stdout, stderr = self.run_command('cleanup_activitystream', days=0)
        cleanup_elapsed = time.time() - t
        self.assertEqual(result, None)
        count_after = ActivityStream.objects.count()
        self.assertNotEqual(count_before, count_after)
        self.assertFalse(count_after)
        self.assertTrue(cleanup_elapsed < (create_elapsed / 4),
                        'create took %0.3fs, cleanup took %0.3fs, expected < %0.3fs' % (create_elapsed, cleanup_elapsed, create_elapsed / 4))
