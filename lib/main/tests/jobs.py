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

import datetime
import json
from django.contrib.auth.models import User as DjangoUser
from django.core.urlresolvers import reverse
from django.test.client import Client
from lib.main.models import *
from lib.main.tests.base import BaseTest

__all__ = ['JobTemplateTest', 'JobTest']

TEST_PLAYBOOK = '''- hosts: mygroup
  gather_facts: false
  tasks:
  - name: woohoo
    command: test 1 = 1
'''

class BaseJobTest(BaseTest):
    ''''''

    def get_other2_credentials(self):
        return ('other2', 'other2')

    def get_nobody_credentials(self):
        return ('nobody', 'nobody')

    def setUp(self):
        super(BaseJobTest, self).setUp()

        # Users
        self.setup_users()
        self.other2_django_user = self.make_user('other2', 'other2')
        self.nobody_django_user = self.make_user('nobody', 'nobody')

        # Organization
        self.organization = Organization.objects.create(
            name='engineering',
            created_by=self.normal_django_user,
        )
        self.organization.admins.add(self.normal_django_user)
        self.organization.users.add(self.normal_django_user)
        self.organization.users.add(self.other_django_user)
        self.organization.users.add(self.other2_django_user)

        # Team
        self.team = self.organization.teams.create(
             name='Tigger',
             created_by=self.normal_django_user,
        )
        self.team.users.add(self.other_django_user)
        self.team.users.add(self.other2_django_user)

        # Project
        self.project = self.make_projects(self.normal_django_user, 1,
                                          playbook_content=TEST_PLAYBOOK)[0]
        self.organization.projects.add(self.project)

        # Inventory
        self.inventory = self.organization.inventories.create(
            name = 'prod',
            created_by = self.normal_django_user,
        )
        self.group_a = self.inventory.groups.create(
            name = 'group1',
            created_by = self.normal_django_user 
        )
        self.host_a = self.inventory.hosts.create(
             name = '127.0.0.1',
             created_by = self.normal_django_user
        )
        self.host_b = self.inventory.hosts.create(
             name = '127.0.0.2',
             created_by = self.normal_django_user
        )
        self.group_a.hosts.add(self.host_a) 
        self.group_a.hosts.add(self.host_b)

        # Credentials
        self.user_credential = self.other_django_user.credentials.create(
            ssh_key_data = 'xxx',
            created_by = self.normal_django_user,
        )
        self.team_credential = self.team.credentials.create(
            ssh_key_data = 'xxx',
            created_by = self.normal_django_user,
        )

        # other django user is on the project team and can deploy
        self.permission1 = Permission.objects.create(
            inventory       = self.inventory,
            project         = self.project,
            team            = self.team, 
            permission_type = PERM_INVENTORY_DEPLOY,
            created_by      = self.normal_django_user
        )
        # individual permission granted to other2 user, can run check mode
        self.permission2 = Permission.objects.create(
            inventory       = self.inventory,
            project         = self.project,
            user            = self.other2_django_user,
            permission_type = PERM_INVENTORY_CHECK,
            created_by      = self.normal_django_user
        )
 
        self.job_template1 = JobTemplate.objects.create(
            name = 'job-run',
            job_type = 'run',
            inventory = self.inventory,
            credential = self.user_credential,
            project = self.project,
            created_by      = self.normal_django_user,
        )        
        self.job_template2 = JobTemplate.objects.create(
            name = 'job-check',
            job_type = 'check',
            inventory = self.inventory,
            credential = self.team_credential,
            project = self.project,
            created_by      = self.normal_django_user,
        )        


class JobTemplateTest(BaseJobTest):

    def setUp(self):
        super(JobTemplateTest, self).setUp()

    def test_job_template_list(self):
        url = reverse('main:job_templates_list')
        
        response = self.get(url, expect=401)
        with self.current_user(self.normal_django_user):
            response = self.get(url, expect=200)
            self.assertTrue(response['count'], JobTemplate.objects.count())

        # FIXME: Test that user can only see job templates from own organization.
        
        # org admin can add job template
        data = dict(
            name         = 'job-foo', 
            credential   = self.user_credential.pk, 
            inventory    = self.inventory.pk, 
            project      = self.project.pk,
            job_type     = PERM_INVENTORY_DEPLOY,
        )
        with self.current_user(self.normal_django_user):
            response = self.post(url, data, expect=201)
            detail_url = reverse('main:job_templates_detail',
                                 args=(response['id'],))
            self.assertEquals(response['url'], detail_url)

        # other_django_user is on a team that can deploy, so can create both
        # deploy and check type job templates
        with self.current_user(self.other_django_user):
            data['name'] = 'job-foo2'
            response = self.post(url, data, expect=201)
            data['name'] = 'job-foo3'
            data['job_type'] = PERM_INVENTORY_CHECK
            response = self.post(url, data, expect=201)

        # other2_django_user has individual permissions to run check mode,
        # but not deploy
        with self.current_user(self.other2_django_user):
            data['name'] = 'job-foo4'
            #data['credential'] = self.user_credential.pk
            #response = self.post(url, data, expect=201)
            data['name'] = 'job-foo5'
            data['job_type'] = PERM_INVENTORY_DEPLOY
            response = self.post(url, data, expect=403)

        # nobody user can't even run check mode
        with self.current_user(self.nobody_django_user):
            data['name'] = 'job-foo5'
            data['job_type'] = PERM_INVENTORY_CHECK
            response = self.post(url, data, expect=403)
            data['job_type'] = PERM_INVENTORY_DEPLOY
            response = self.post(url, data, expect=403)

    def test_job_template_detail(self):
        
        return # FIXME
        # verify we can also get the job template record
        got = self.get(url, expect=200, auth=self.get_other2_credentials())
        self.failUnlessEqual(got['url'], '/api/v1/job_templates/6/')

        # TODO: add more tests that show
        # the method used to START a JobTemplate follow the exact same permissions as those to create it ...
        # and that jobs come back nicely serialized with related resources and so on ...
        # that we can drill all the way down and can get at host failure lists, etc ...





class JobTest(BaseJobTest):

    def setUp(self):
        super(JobTest, self).setUp()

    def test_mainline(self):

        return # FIXME
        
        # job templates
        data = self.get('/api/v1/job_templates/', expect=401)
        data = self.get('/api/v1/job_templates/', expect=200, auth=self.get_normal_credentials())
        self.assertTrue(data['count'], 2)
        
        rec = dict(
            name         = 'job-foo', 
            credential   = self.credential.pk, 
            inventory    = self.inventory.pk, 
            project      = self.project.pk,
            job_type     = PERM_INVENTORY_DEPLOY
        )

        # org admin can add job type
        posted = self.post('/api/v1/job_templates/', rec, expect=201, auth=self.get_normal_credentials())
        self.assertEquals(posted['url'], '/api/v1/job_templates/3/')

        # other_django_user is on a team that can deploy, so can create both deploy and check type jobs
        rec['name'] = 'job-foo2' 
        posted = self.post('/api/v1/job_templates/', rec, expect=201, auth=self.get_other_credentials())
        rec['name'] = 'job-foo3'
        rec['job_type'] = PERM_INVENTORY_CHECK
        posted = self.post('/api/v1/job_templates/', rec, expect=201, auth=self.get_other_credentials())

        # other2_django_user has individual permissions to run check mode, but not deploy
        # nobody user can't even run check mode
        rec['name'] = 'job-foo4'
        self.post('/api/v1/job_templates/', rec, expect=403, auth=self.get_nobody_credentials())
        rec['credential'] = self.credential2.pk
        posted = self.post('/api/v1/job_templates/', rec, expect=201, auth=self.get_other2_credentials())
        rec['name'] = 'job-foo5'
        rec['job_type'] = PERM_INVENTORY_DEPLOY
        self.post('/api/v1/job_templates/', rec, expect=403, auth=self.get_nobody_credentials())
        self.post('/api/v1/job_templates/', rec, expect=201, auth=self.get_other2_credentials())
        url = posted['url']

        # verify we can also get the job template record
        got = self.get(url, expect=200, auth=self.get_other2_credentials())
        self.failUnlessEqual(got['url'], '/api/v1/job_templates/6/')

        # TODO: add more tests that show
        # the method used to START a JobTemplate follow the exact same permissions as those to create it ...
        # and that jobs come back nicely serialized with related resources and so on ...
        # that we can drill all the way down and can get at host failure lists, etc ...


