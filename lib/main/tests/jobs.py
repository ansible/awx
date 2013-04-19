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
import django.test
from django.test.client import Client
from lib.main.models import *
from lib.main.tests.base import BaseTest

class JobsTest(BaseTest):

    def collection(self):
        # not really used
        return '/api/v1/job_templates/'

    def get_other2_credentials(self):
        return ('other2', 'other2')

    def get_nobody_credentials(self):
        return ('nobody', 'nobody')

    def setUp(self):
        super(JobsTest, self).setUp()
        self.setup_users()

        self.other2_django_user = User.objects.create(username='other2')
        self.other2_django_user.set_password('other2')
        self.other2_django_user.save()
        self.nobody_django_user = User.objects.create(username='nobody')
        self.nobody_django_user.set_password('nobody')
        self.nobody_django_user.save()
 
        self.organization = Organization.objects.create(
            name = 'engineering',
            created_by = self.normal_django_user
        )
 
        self.inventory = Inventory.objects.create(
            name = 'prod',
            organization = self.organization,
            created_by = self.normal_django_user 
        )

        self.group_a = Group.objects.create(
            name = 'group1',
            inventory = self.inventory,
            created_by = self.normal_django_user 
        )

        self.team = Team.objects.create(
             name = 'Tigger',
             created_by = self.normal_django_user
        )

        self.team.users.add(self.other_django_user)

        self.project = Project.objects.create(
            name = 'testProject',
            created_by = self.normal_django_user,
            local_repository = '/tmp/',
            scm_type = 'git',
            default_playbook = 'site.yml',
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
 
        self.host_a = Host.objects.create(
             name = '127.0.0.1',
             inventory = self.inventory,
             created_by = self.normal_django_user
        )

        self.host_b = Host.objects.create(
             name = '127.0.0.2',
             inventory = self.inventory,
             created_by = self.normal_django_user
        )

        self.group_a.hosts.add(self.host_a) 
        self.group_a.hosts.add(self.host_b)
        self.group_a.save()


        self.credential = Credential.objects.create(
            ssh_key_data = 'xxx',
            created_by = self.normal_django_user
        )

        self.organization.projects.add(self.project)
        self.organization.admins.add(self.normal_django_user)
        self.organization.users.add(self.normal_django_user)
        self.organization.save()

        self.template1 = JobTemplate.objects.create(
            name = 'job-run',
            job_type = 'run',
            inventory = self.inventory,
            credential = self.credential,
            project = self.project,
        )        
        self.template2 = JobTemplate.objects.create(
            name = 'job-check',
            job_type = 'check',
            inventory = self.inventory,
            credential = self.credential,
            project = self.project,
        )        


    def test_mainline(self):

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
        posted = self.post('/api/v1/job_templates/', rec, expect=403, auth=self.get_nobody_credentials())
        posted = self.post('/api/v1/job_templates/', rec, expect=201, auth=self.get_other2_credentials())
        rec['name'] = 'job-foo5'
        rec['job_type'] = PERM_INVENTORY_DEPLOY
        posted = self.post('/api/v1/job_templates/', rec, expect=403, auth=self.get_nobody_credentials())
        posted = self.post('/api/v1/job_templates/', rec, expect=403, auth=self.get_other2_credentials())

        # TODO: add more tests that show
        # the method used to START a JobTemplate follow the exact same permissions as those to create it ...
        # and that jobs come back nicely serialized with related resources and so on ...
        # that we can drill all the way down and can get at host failure lists, etc ...


