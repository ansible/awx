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

TEST_PLAYBOOK = '''- hosts: all
  gather_facts: false
  tasks:
  - name: woohoo
    command: test 1 = 1
'''

class BaseJobTest(BaseTest):
    ''''''

    def _create_inventory(self, name, organization, created_by,
                          groups_hosts_dict):
        '''Helper method for creating inventory with groups and hosts.'''
        inventory = organization.inventories.create(
            name=name,
            created_by=created_by,
        )
        for group_name, host_names in groups_hosts_dict.items():
            group = inventory.groups.create(
                name=group_name,
                created_by=created_by,
            )
            for host_name in host_names:
                host = inventory.hosts.create(
                    name=host_name,
                    created_by=created_by,
                )
                group.hosts.add(host)
        return inventory

    def populate(self):
        # Here's a little story about the Ansible Bread Company, or ABC.  They
        # make machines that make bread - bakers, slicers, and packagers - and
        # these machines are each controlled by a Linux boxes, which is in turn
        # managed by Ansible Commander.

        # Sue is the super user.  You don't mess with Sue or you're toast. Ha.
        self.user_sue = self.make_user('sue', super_user=True)

        # There are three organizations in ABC using Ansible, since it's the
        # best thing for dev ops automation since, well, sliced bread.

        # Engineering - They design and build the machines.
        self.org_eng = Organization.objects.create(
            name='engineering',
            created_by=self.user_sue,
        )
        # Support - They fix it when it's not working.
        self.org_sup = Organization.objects.create(
            name='support',
            created_by=self.user_sue,
        )
        # Operations - They implement the production lines using the machines.
        self.org_ops = Organization.objects.create(
            name='operations',
            created_by=self.user_sue,
        )

        # Alex is Sue's IT assistant who can also administer all of the
        # organizations.
        self.user_alex = self.make_user('alex')
        self.org_eng.admins.add(self.user_alex)
        self.org_sup.admins.add(self.user_alex)
        self.org_ops.admins.add(self.user_alex)

        # Bob is the head of engineering.  He's an admin for engineering, but
        # also a user within the operations organization (so he can see the
        # results if things go wrong in production).
        self.user_bob = self.make_user('bob')
        self.org_eng.admins.add(self.user_bob)
        self.org_ops.users.add(self.user_bob)

        # Chuck is the lead engineer.  He has full reign over engineering, but
        # no other organizations.
        self.user_chuck = self.make_user('chuck')
        self.org_eng.admins.add(self.user_chuck)

        # Doug is the other engineer working under Chuck.  He can write
        # playbooks and check them, but Chuck doesn't quite think he's ready to
        # run them yet.  Poor Doug.
        self.user_doug = self.make_user('doug')
        self.org_eng.users.add(self.user_doug)

        # Eve is the head of support.  She can also see what goes on in
        # operations to help them troubleshoot problems.
        self.user_eve = self.make_user('eve')
        self.org_sup.admins.add(self.user_eve)
        self.org_ops.users.add(self.user_eve)

        # Frank is the other support guy.
        self.user_frank = self.make_user('frank')
        self.org_sup.users.add(self.user_frank)

        # Greg is the head of operations.
        self.user_greg = self.make_user('greg')
        self.org_ops.admins.add(self.user_greg)

        # Holly is an operations engineer.
        self.user_holly = self.make_user('holly')
        self.org_ops.users.add(self.user_holly)

        # Iris is another operations engineer.
        self.user_iris = self.make_user('iris')
        self.org_ops.users.add(self.user_iris)
        
        # Jim is the intern. He can login, but can't do anything quite yet
        # except make everyone else fresh coffee.
        self.user_jim = self.make_user('jim')

        # There are three main projects, one each for the development, test and
        # production branches of the playbook repository.  All three orgs can
        # use the production branch, support can use the production and testing
        # branches, and operations can only use the production branch.
        self.proj_dev = self.make_project('dev', 'development branch',
                                          self.user_sue, TEST_PLAYBOOK)
        self.org_eng.projects.add(self.proj_dev)
        self.proj_test = self.make_project('test', 'testing branch',
                                           self.user_sue, TEST_PLAYBOOK)
        self.org_eng.projects.add(self.proj_test)
        self.org_sup.projects.add(self.proj_test)
        self.proj_prod = self.make_project('prod', 'production branch',
                                           self.user_sue, TEST_PLAYBOOK)
        self.org_eng.projects.add(self.proj_prod)
        self.org_sup.projects.add(self.proj_prod)
        self.org_ops.projects.add(self.proj_prod)

        # Operations also has 2 additional projects specific to the east/west
        # production environments.
        self.proj_prod_east = self.make_project('prod-east',
                                                'east production branch',
                                                self.user_sue, TEST_PLAYBOOK)
        self.org_ops.projects.add(self.proj_prod_east)
        self.proj_prod_west = self.make_project('prod-west',
                                                'west production branch',
                                                self.user_sue, TEST_PLAYBOOK)
        self.org_ops.projects.add(self.proj_prod_west)

        # The engineering organization has a set of servers to use for
        # development and testing (2 bakers, 1 slicer, 1 packager).
        self.inv_eng = self._create_inventory(
            name='engineering environment',
            organization=self.org_eng,
            created_by=self.user_sue,
            groups_hosts_dict={
                'bakers': ['eng-baker1', 'eng-baker2'],
                'slicers': ['eng-slicer1'],
                'packagers': ['eng-packager1'],
            },
        )

        # The support organization has a set of servers to use for
        # testing and reproducing problems from operations (1 baker, 1 slicer,
        # 1 packager).
        self.inv_sup = self._create_inventory(
            name='support environment',
            organization=self.org_sup,
            created_by=self.user_sue,
            groups_hosts_dict={
                'bakers': ['sup-baker1'],
                'slicers': ['sup-slicer1'],
                'packagers': ['sup-packager1'],
            },
        )

        # The operations organization manages multiple sets of servers for the
        # east and west production facilities.
        self.inv_ops_east = self._create_inventory(
            name='east production environment',
            organization=self.org_ops,
            created_by=self.user_sue,
            groups_hosts_dict={
                'bakers': ['east-baker%d' % n for n in range(1, 4)],
                'slicers': ['east-slicer%d' % n for n in range(1, 3)],
                'packagers': ['east-packager%d' % n for n in range(1, 3)],
            },
        )
        self.inv_ops_west = self._create_inventory(
            name='west production environment',
            organization=self.org_ops,
            created_by=self.user_sue,
            groups_hosts_dict={
                'bakers': ['west-baker%d' % n for n in range(1, 6)],
                'slicers': ['west-slicer%d' % n for n in range(1, 4)],
                'packagers': ['west-packager%d' % n for n in range(1, 3)],
            },
        )

        # Operations is divided into teams to work on the east/west servers.
        # Greg and Holly work on east, Greg and iris work on west.
        self.team_ops_east = self.org_ops.teams.create(
             name='easterners',
             created_by=self.user_sue,
        )
        self.team_ops_east.projects.add(self.proj_prod)
        self.team_ops_east.projects.add(self.proj_prod_east)
        self.team_ops_east.users.add(self.user_greg)
        self.team_ops_east.users.add(self.user_holly)
        self.team_ops_west = self.org_ops.teams.create(
             name='westerners',
             created_by=self.user_sue,
        )
        self.team_ops_west.projects.add(self.proj_prod)
        self.team_ops_west.projects.add(self.proj_prod_west)
        self.team_ops_west.users.add(self.user_greg)
        self.team_ops_west.users.add(self.user_iris)

        # Each user has his/her own set of credentials.
        from lib.main.tests.tasks import (TEST_SSH_KEY_DATA,
                                          TEST_SSH_KEY_DATA_LOCKED,
                                          TEST_SSH_KEY_DATA_UNLOCK)
        self.cred_bob = self.user_bob.credentials.create(
            ssh_username='bob',
            ssh_password='ASK',
            created_by=self.user_sue,
        )
        self.cred_chuck = self.user_chuck.credentials.create(
            ssh_username='chuck',
            ssh_key_data=TEST_SSH_KEY_DATA,
            created_by=self.user_sue,
        )
        self.cred_doug = self.user_doug.credentials.create(
            ssh_username='doug',
            ssh_password='doug doesn\'t mind his password being saved. this '
                         'is why we dont\'t let doug actually run jobs.',
            created_by=self.user_sue,
        )
        self.cred_eve = self.user_eve.credentials.create(
            ssh_username='eve',
            ssh_password='ASK',
            created_by=self.user_sue,
        )
        self.cred_frank = self.user_frank.credentials.create(
            ssh_username='frank',
            ssh_password='fr@nk the t@nk',
            created_by=self.user_sue,
        )
        self.cred_greg = self.user_greg.credentials.create(
            ssh_username='greg',
            ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
            ssh_key_unlock='ASK',
            created_by=self.user_sue,
        )
        self.cred_holly = self.user_holly.credentials.create(
            ssh_username='holly',
            ssh_password='holly rocks',
            created_by=self.user_sue,
        )
        self.cred_iris = self.user_iris.credentials.create(
            ssh_username='iris',
            ssh_password='',
            created_by=self.user_sue,
        )

        # Each operations team also has shared credentials they can use.
        self.cred_ops_east = self.team_ops_east.credentials.create(
            ssh_username='east',
            ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
            ssh_key_unlock=TEST_SSH_KEY_DATA_UNLOCK,
            created_by = self.user_sue,
        )
        self.cred_ops_west = self.team_ops_west.credentials.create(
            ssh_username='west',
            ssh_password='Heading270',
            created_by = self.user_sue,
        )

        # FIXME: Define explicit permissions for tests.
        # other django user is on the project team and can deploy
        #self.permission1 = Permission.objects.create(
        #    inventory       = self.inventory,
        #    project         = self.project,
        #    team            = self.team, 
        #    permission_type = PERM_INVENTORY_DEPLOY,
        #    created_by      = self.normal_django_user
        #)
        # individual permission granted to other2 user, can run check mode
        #self.permission2 = Permission.objects.create(
        #    inventory       = self.inventory,
        #    project         = self.project,
        #    user            = self.other2_django_user,
        #    permission_type = PERM_INVENTORY_CHECK,
        #    created_by      = self.normal_django_user
        #)
 
        # Engineering has job templates to check/run the dev project onto
        # their own inventory.
        self.jt_eng_check = JobTemplate.objects.create(
            name='eng-dev-check',
            job_type='check',
            inventory= self.inv_eng,
            project=self.proj_dev,
            playbook=self.proj_dev.playbooks[0],
            created_by=self.user_sue,
        )
        self.job_eng_check = self.jt_eng_check.create_job(
            created_by=self.user_sue,
            credential=self.cred_doug,
        )
        self.jt_eng_run = JobTemplate.objects.create(
            name='eng-dev-run',
            job_type='run',
            inventory= self.inv_eng,
            project=self.proj_dev,
            playbook=self.proj_dev.playbooks[0],
            created_by=self.user_sue,
        )
        self.job_eng_run = self.jt_eng_run.create_job(
            created_by=self.user_sue,
            credential=self.cred_chuck,
        )

        # Support has job templates to check/run the test project onto
        # their own inventory.
        self.jt_sup_check = JobTemplate.objects.create(
            name='sup-test-check',
            job_type='check',
            inventory= self.inv_sup,
            project=self.proj_test,
            playbook=self.proj_test.playbooks[0],
            created_by=self.user_sue,
        )
        self.job_sup_check = self.jt_sup_check.create_job(
            created_by=self.user_sue,
            credential=self.cred_frank,
        )
        self.jt_sup_run = JobTemplate.objects.create(
            name='sup-test-run',
            job_type='run',
            inventory= self.inv_sup,
            project=self.proj_test,
            playbook=self.proj_test.playbooks[0],
            created_by=self.user_sue,
        )
        self.job_sup_run = self.jt_sup_run.create_job(
            created_by=self.user_sue,
            credential=self.cred_eve,
        )

        # Operations has job templates to check/run the prod project onto
        # both east and west inventories, by default using the team credential.
        self.jt_ops_east_check = JobTemplate.objects.create(
            name='ops-east-prod-check',
            job_type='check',
            inventory= self.inv_ops_east,
            project=self.proj_prod,
            playbook=self.proj_prod.playbooks[0],
            credential=self.cred_ops_east,
            created_by=self.user_sue,
        )
        self.job_ops_east_check = self.jt_ops_east_check.create_job(
            created_by=self.user_sue,
        )
        self.jt_ops_east_run = JobTemplate.objects.create(
            name='ops-east-prod-run',
            job_type='run',
            inventory= self.inv_ops_east,
            project=self.proj_prod,
            playbook=self.proj_prod.playbooks[0],
            credential=self.cred_ops_east,
            created_by=self.user_sue,
        )
        self.job_ops_east_run = self.jt_ops_east_run.create_job(
            created_by=self.user_sue,
        )
        self.jt_ops_west_check = JobTemplate.objects.create(
            name='ops-west-prod-check',
            job_type='check',
            inventory= self.inv_ops_west,
            project=self.proj_prod,
            playbook=self.proj_prod.playbooks[0],
            credential=self.cred_ops_west,
            created_by=self.user_sue,
        )
        self.job_ops_west_check = self.jt_ops_west_check.create_job(
            created_by=self.user_sue,
        )
        self.jt_ops_west_run = JobTemplate.objects.create(
            name='ops-west-prod-run',
            job_type='run',
            inventory= self.inv_ops_west,
            project=self.proj_prod,
            playbook=self.proj_prod.playbooks[0],
            credential=self.cred_ops_west,
            created_by=self.user_sue,
        )
        self.job_ops_west_run = self.jt_ops_west_run.create_job(
            created_by=self.user_sue,
        )

    def setUp(self):
        super(BaseJobTest, self).setUp()
        self.populate()


class JobTemplateTest(BaseJobTest):

    def setUp(self):
        super(JobTemplateTest, self).setUp()

    def _test_invalid_creds(self, url, data=None, methods=None):
        data = data or {}
        methods = methods or ('options', 'head', 'get')
        for auth in [(None,), ('invalid', 'password')]:
            with self.current_user(*auth):
                for method in methods:
                    f = getattr(self, method)
                    if method in ('post', 'put'):
                        f(url, data, expect=401)
                    else:
                        f(url, expect=401)

    def test_get_job_template_list(self):
        url = reverse('main:job_template_list')

        # Test with no auth and with invalid login.
        self._test_invalid_creds(url)

        # sue's credentials (superuser) == 200, full list
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
        qs = JobTemplate.objects.all()
        self.check_pagination_and_size(response, qs.count())
        self.check_list_ids(response, qs)

        # FIXME: Check individual job template result fields.

        # alex's credentials (admin of all orgs) == 200, full list
        with self.current_user(self.user_alex):
            self.options(url)
            self.head(url)
            response = self.get(url)
        qs = JobTemplate.objects.all()
        self.check_pagination_and_size(response, qs.count())
        self.check_list_ids(response, qs)

        # bob's credentials (admin of eng, user of ops) == 200, all from
        # engineering and operations.
        with self.current_user(self.user_bob):
            self.options(url)
            self.head(url)
            response = self.get(url)
        qs = JobTemplate.objects.filter(
            inventory__organization__in=[self.org_eng, self.org_ops],
        )
        #self.check_pagination_and_size(response, qs.count())
        #self.check_list_ids(response, qs)

        # FIXME: Check with other credentials.

    def test_post_job_template_list(self):
        url = reverse('main:job_template_list')
        data = dict(
            name         = 'new job template',
            job_type     = PERM_INVENTORY_DEPLOY,
            inventory    = self.inv_eng.pk,
            project      = self.proj_dev.pk,
            playbook     = self.proj_dev.playbooks[0],
        )

        # Test with no auth and with invalid login.
        self._test_invalid_creds(url, data, methods=('post',))

        # sue can always add job templates.
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)
            detail_url = reverse('main:job_template_detail',
                                 args=(response['id'],))
            self.assertEquals(response['url'], detail_url)

        # Check that all fields provided were set.
        jt = JobTemplate.objects.get(pk=response['id'])
        self.assertEqual(jt.name, data['name'])
        self.assertEqual(jt.job_type, data['job_type'])
        self.assertEqual(jt.inventory.pk, data['inventory'])
        self.assertEqual(jt.credential, None)
        self.assertEqual(jt.project.pk, data['project'])
        self.assertEqual(jt.playbook, data['playbook'])

        # Test that all required fields are really required.
        data['name'] = 'another new job template'
        for field in ('name', 'job_type', 'inventory', 'project', 'playbook'):
            with self.current_user(self.user_sue):
                d = dict(data.items())
                d.pop(field)
                response = self.post(url, d, expect=400)
                self.assertTrue(field in response,
                                'no error for field "%s" in response' % field)

        # Test invalid value for job_type.
        with self.current_user(self.user_sue):
            d = dict(data.items())
            d['job_type'] = 'world domination'
            response = self.post(url, d, expect=400)
            self.assertTrue('job_type' in response)
    
        # Test playbook not in list of project playbooks.
        with self.current_user(self.user_sue):
            d = dict(data.items())
            d['playbook'] = 'no_playbook_here.yml'
            response = self.post(url, d, expect=400)
            self.assertTrue('playbook' in response)

        # FIXME: Check other credentials and optional fields.

    def test_get_job_template_detail(self):
        jt = self.jt_eng_run
        url = reverse('main:job_template_detail', args=(jt.pk,))

        # Test with no auth and with invalid login.
        self._test_invalid_creds(url)

        # sue can read the job template detail.
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
            self.assertEqual(response['url'], url)

        # FIXME: Check other credentials and optional fields.

        # TODO: add more tests that show
        # the method used to START a JobTemplate follow the exact same permissions as those to create it ...
        # and that jobs come back nicely serialized with related resources and so on ...
        # that we can drill all the way down and can get at host failure lists, etc ...

    def test_put_job_template_detail(self):
        jt = self.jt_eng_run
        url = reverse('main:job_template_detail', args=(jt.pk,))

        # Test with no auth and with invalid login.
        self._test_invalid_creds(url, methods=('put',))

        # sue can update the job template detail.
        with self.current_user(self.user_sue):
            data = self.get(url)
            response = self.put(url, data)

        # FIXME: Check other credentials and optional fields.

    def test_get_job_template_job_list(self):
        jt = self.jt_eng_run
        url = reverse('main:job_template_job_list', args=(jt.pk,))

        # Test with no auth and with invalid login.
        self._test_invalid_creds(url)

        # sue can read the job template job list.
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
        qs = jt.jobs.all()
        self.check_pagination_and_size(response, qs.count())
        self.check_list_ids(response, qs)

        # FIXME: Check other credentials and optional fields.

    def test_post_job_template_job_list(self):
        jt = self.jt_eng_run
        url = reverse('main:job_template_job_list', args=(jt.pk,))
        data = dict(
            name='new job from template',
            credential=self.cred_bob.pk,
        )

        # Test with no auth and with invalid login.
        self._test_invalid_creds(url, data, methods=('post',))

        # sue can create a new job from the template.
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)

        # FIXME: Check other credentials and optional fields.

class JobTest(BaseJobTest):

    def setUp(self):
        super(JobTest, self).setUp()

    def test_get_job_list(self):
        pass

    def test_post_job_list(self):
        pass

    def test_get_job_detail(self):
        pass

    def test_put_job_detail(self):
        pass

    def test_get_job_start(self):
        pass

    def test_post_job_start(self):
        pass

    def test_get_job_cancel(self):
        pass

    def test_post_job_cancel(self):
        pass

    def test_get_job_host_list(self):
        pass

    def test_get_job_job_event_list(self):
        pass

    def _test_mainline(self):
        url = reverse('main:job_list')

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


