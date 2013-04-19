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

    def setUp(self):
        super(JobsTest, self).setUp()
        self.setup_users()
 
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

        self.project = Project.objects.create(
            name = 'testProject',
            created_by = self.normal_django_user,
            local_repository = '/tmp/',
            scm_type = 'git',
            default_playbook = 'site.yml',
        )

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


    def test_get_list(self):

        # no credentials == 401
        data = self.get('/api/v1/job_templates/', expect=401)
        data = self.get('/api/v1/job_templates/', expect=200, auth=self.get_normal_credentials())
        #print data
        self.assertTrue(data['count'], 99)


