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
import shutil
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
        # Pass test database name in environment for use by the inventory script.
        os.environ['ACOM_TEST_DATABASE_NAME'] = settings.DATABASES['default']['NAME']

    def tearDown(self):
        super(RunJobTest, self).tearDown()
        os.environ.pop('ACOM_TEST_DATABASE_NAME', None)
        if self.test_project_path:
            shutil.rmtree(self.test_project_path, True)

    def create_test_project(self, playbook_content):
        self.project = self.make_projects(self.normal_django_user, 1, playbook_content)[0]
        self.organization.projects.add(self.project)

    def create_test_job(self, **kwargs):
        opts = {
            'name': 'test-job-template',
            'inventory': self.inventory,
            'project': self.project,
            'playbook': self.project.available_playbooks[0],
        }
        opts.update(kwargs)
        self.job_template = JobTemplate.objects.create(**opts)
        return self.job_template.create_job()

    def test_run_job(self):
        self.create_test_project(TEST_PLAYBOOK)
        job = self.create_test_job()
        self.assertEqual(job.status, 'new')
        job.start()
        self.assertEqual(job.status, 'pending')
        job = Job.objects.get(pk=job.pk)
        #print 'stdout:', job.result_stdout
        #print 'stderr:', job.result_stderr
        #print job.status
        #print settings.DATABASES
        self.assertEqual(job.status, 'successful')
        self.assertTrue(job.result_stdout)
        job_events = job.job_events.all()
        self.assertEqual(job_events.filter(event='playbook_on_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_play_start').count(), 1)
        self.assertEqual(job_events.filter(event='playbook_on_task_start').count(), 2)
        self.assertEqual(job_events.filter(event='runner_on_ok').count(), 2)
        for evt in job_events.filter(event='runner_on_ok'):
            self.assertEqual(evt.host, self.host)
        self.assertEqual(job_events.filter(event='playbook_on_stats').count(), 1)
        self.assertEqual(job.successful_hosts.count(), 1)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 1)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_check_job(self):
        self.create_test_project(TEST_PLAYBOOK)
        job = self.create_test_job(job_type='check')
        self.assertEqual(job.status, 'new')
        job.start()
        self.assertEqual(job.status, 'pending')
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
        self.assertEqual(job.successful_hosts.count(), 0)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 1)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_run_job_that_fails(self):
        self.create_test_project(TEST_PLAYBOOK2)
        job = self.create_test_job()
        self.assertEqual(job.status, 'new')
        job.start()
        self.assertEqual(job.status, 'pending')
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
        self.assertEqual(job.successful_hosts.count(), 0)
        self.assertEqual(job.failed_hosts.count(), 1)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_check_job_where_task_would_fail(self):
        self.create_test_project(TEST_PLAYBOOK2)
        job = self.create_test_job(job_type='check')
        self.assertEqual(job.status, 'new')
        job.start()
        self.assertEqual(job.status, 'pending')
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
        self.assertEqual(job.successful_hosts.count(), 0)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 1)
        self.assertEqual(job.processed_hosts.count(), 1)
