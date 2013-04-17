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


import os
import tempfile
from django.conf import settings
from django.test.utils import override_settings
from lib.main.models import *
from lib.main.tests.base import BaseTransactionTest

TEST_PLAYBOOK = '''- hosts: test-group
  gather_facts: False
  tasks:
  - name: should pass
    command: test 1 = 1
  - name: should also pass
    command: test 2 = 2
'''

TEST_PLAYBOOK2 = '''- hosts: test-group
  gather_facts: False
  tasks:
  - name: should fail
    command: test 1 = 0
'''

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class BaseCeleryTest(BaseTransactionTest):
    '''
    Base class for celery task tests.
    '''

@override_settings(ANSIBLE_TRANSPORT='local')
class RunJobTest(BaseCeleryTest):
    '''
    Test cases for run_job celery task.
    '''

    def setUp(self):
        super(RunJobTest, self).setUp()
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.project = self.make_projects(self.normal_django_user, 1)[0]
        self.organization.projects.add(self.project)
        self.inventory = Inventory.objects.create(name='test-inventory',
                                                  description='description for test-inventory',
                                                  organization=self.organization)
        self.host = self.inventory.hosts.create(name='host.example.com',
                                                inventory=self.inventory)
        self.group = self.inventory.groups.create(name='test-group',
                                                  inventory=self.inventory)
        self.group.hosts.add(self.host)
        # Pass test database name in environment for use by the inventory script.
        os.environ['ACOM_TEST_DATABASE_NAME'] = settings.DATABASES['default']['NAME']

    def tearDown(self):
        super(RunJobTest, self).tearDown()
        os.environ.pop('ACOM_TEST_DATABASE_NAME', None)
        os.remove(self.test_playbook)

    def create_test_playbook(self, s):
        handle, self.test_playbook = tempfile.mkstemp(suffix='.yml', prefix='playbook-')
        test_playbook_file = os.fdopen(handle, 'w')
        test_playbook_file.write(s)
        test_playbook_file.close()
        self.project.default_playbook = self.test_playbook
        self.project.save()

    def test_run_job(self):
        self.create_test_playbook(TEST_PLAYBOOK)
        job = Job.objects.create(name='test-job', inventory=self.inventory,
                                 project=self.project)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(set(job.hosts.values_list('pk', flat=True)),
                         set([self.host.pk]))
        job = Job.objects.get(pk=job.pk)
        #print 'stdout:', launch_job_status.result_stdout
        #print 'stderr:', launch_job_status.result_stderr
        #print launch_job_status.status
        #print settings.DATABASES
        self.assertEqual(job.status, 'successful')
        self.assertTrue(job.result_stdout)
        job_events = job.job_events.all()
        #for ev in launch_job_status_events:
        #    print ev.event, ev.event_data
        self.assertEqual(job_events.filter(event='playbook_on_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_play_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_task_start').count(), 2)
        self.assertEqual(job_events.filter(event='runner_on_ok').count(), 2)
        for evt in job_events.filter(event='runner_on_ok'):
            self.assertEqual(evt.host, self.host)
        self.assertEqual(job_events.filter(event='playbook_on_stats').count(), 1)

    def test_check_job(self):
        self.create_test_playbook(TEST_PLAYBOOK)
        job = Job.objects.create(name='test-job', inventory=self.inventory,
                                 project=self.project, job_type='check')
        self.assertEqual(job.status, 'pending')
        self.assertEqual(set(job.hosts.values_list('pk', flat=True)),
                         set([self.host.pk]))
        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, 'successful')
        self.assertTrue(job.result_stdout)
        job_events = job.job_events.all()
        self.assertEqual(job_events.filter(event='playbook_on_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_play_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_task_start').count(), 2)
        self.assertEqual(job_events.filter(event='runner_on_skipped').count(), 2)
        for evt in job_events.filter(event='runner_on_skipped'):
            self.assertEqual(evt.host, self.host)
        self.assertEqual(job_events.filter(event='playbook_on_stats').count(), 1)

    def test_run_job_that_fails(self):
        self.create_test_playbook(TEST_PLAYBOOK2)
        job = Job.objects.create(name='test-job', inventory=self.inventory,
                                 project=self.project)
        self.assertEqual(job.status, 'pending')
        self.assertEqual(set(job.hosts.values_list('pk', flat=True)),
                         set([self.host.pk]))
        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, 'failed')
        self.assertTrue(job.result_stdout)
        job_events = job.job_events.all()
        self.assertEqual(job_events.filter(event='playbook_on_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_play_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_task_start').count(), 1)
        self.assertEqual(job_events.filter(event='runner_on_failed').count(), 1)
        self.assertEqual(job_events.get(event='runner_on_failed').host, self.host)
        self.assertEqual(job_events.filter(event='playbook_on_stats').count(), 1)

    def test_check_job_where_task_would_fail(self):
        self.create_test_playbook(TEST_PLAYBOOK2)
        job = Job.objects.create(name='test-job', inventory=self.inventory,
                                 project=self.project, job_type='check')
        self.assertEqual(job.status, 'pending')
        self.assertEqual(set(job.hosts.values_list('pk', flat=True)),
                         set([self.host.pk]))
        job = Job.objects.get(pk=job.pk)
        # Since we don't actually run the task, the --check should indicate
        # everything is successful.
        self.assertEqual(job.status, 'successful')
        self.assertTrue(job.result_stdout)
        job_events = job.job_events.all()
        self.assertEqual(job_events.filter(event='playbook_on_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_play_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_task_start').count(), 1)
        self.assertEqual(job_events.filter(event='runner_on_skipped').count(), 1)
        self.assertEqual(job_events.get(event='runner_on_skipped').host, self.host)
        self.assertEqual(job_events.filter(event='playbook_on_stats').count(), 1)
