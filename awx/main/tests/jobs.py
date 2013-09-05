# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import json
import socket
import struct
import uuid

# Django
from django.contrib.auth.models import User as DjangoUser
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
import django.test
from django.test.client import Client
from django.test.utils import override_settings

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseTestMixin

__all__ = ['JobTemplateTest', 'JobTest', 'JobStartCancelTest',
           'JobTemplateCallbackTest']

TEST_PLAYBOOK = '''- hosts: all
  gather_facts: false
  tasks:
  - name: woohoo
    command: test 1 = 1
'''

class BaseJobTestMixin(BaseTestMixin):
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
        from awx.main.tests.tasks import (TEST_SSH_KEY_DATA,
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
            sudo_username='root',
            sudo_password='ASK',
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
            ssh_password='ASK',
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
            host_config_key=uuid.uuid4().hex,
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
            host_config_key=uuid.uuid4().hex,
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
            host_config_key=uuid.uuid4().hex,
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
            host_config_key=uuid.uuid4().hex,
            credential=self.cred_eve,
            created_by=self.user_sue,
        )
        self.job_sup_run = self.jt_sup_run.create_job(
            created_by=self.user_sue,
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
            host_config_key=uuid.uuid4().hex,
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
            host_config_key=uuid.uuid4().hex,
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
            host_config_key=uuid.uuid4().hex,
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
            host_config_key=uuid.uuid4().hex,
            created_by=self.user_sue,
        )
        self.job_ops_west_run = self.jt_ops_west_run.create_job(
            created_by=self.user_sue,
        )

    def setUp(self):
        super(BaseJobTestMixin, self).setUp()
        self.populate()

class JobTemplateTest(BaseJobTestMixin, django.test.TestCase):

    JOB_TEMPLATE_FIELDS = ('id', 'url', 'related', 'summary_fields', 'created',
                           'modified', 'name', 'description', 'job_type',
                           'inventory', 'project', 'playbook', 'credential',
                           'forks', 'limit', 'verbosity', 'extra_vars',
                           'job_tags', 'host_config_key',)

    def test_get_job_template_list(self):
        url = reverse('main:job_template_list')
        qs = JobTemplate.objects.distinct()
        fields = self.JOB_TEMPLATE_FIELDS

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

        # Sue's credentials (superuser) == 200, full list
        self.check_get_list(url, self.user_sue, qs, fields)
        
        # Alex's credentials (admin of all orgs) == 200, full list
        self.check_get_list(url, self.user_alex, qs, fields)

        # Bob's credentials (admin of eng, user of ops) == 200, all from
        # engineering and operations.
        bob_qs = qs.filter(
            Q(project__organizations__admins__in=[self.user_bob]) |
            Q(project__teams__users__in=[self.user_bob]),
        )
        #self.check_get_list(url, self.user_bob, bob_qs, fields)

        # Chuck's credentials (admin of eng) == 200, all from engineering.
        chuck_qs = qs.filter(
            Q(project__organizations__admins__in=[self.user_chuck]) |
            Q(project__teams__users__in=[self.user_chuck]),
        )
        #self.check_get_list(url, self.user_chuck, chuck_qs, fields)

        # Doug's credentials (user of eng) == 200, none?.
        doug_qs = qs.filter(
            Q(project__organizations__admins__in=[self.user_doug]) |
            Q(project__teams__users__in=[self.user_doug]),
        )
        #self.check_get_list(url, self.user_doug, doug_qs, fields)

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
        self.check_invalid_auth(url, data, methods=('post',))

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
        self.check_invalid_auth(url)

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
        self.check_invalid_auth(url, methods=('put',))# 'patch'))

        # sue can update the job template detail.
        with self.current_user(self.user_sue):
            data = self.get(url)
            data['name'] = '%s-updated' % data['name']
            response = self.put(url, data)
            #patch_data = dict(name='%s-changed' % data['name'])
            #response = self.patch(url, patch_data)

        # FIXME: Check other credentials and optional fields.

    def test_get_job_template_job_list(self):
        jt = self.jt_eng_run
        url = reverse('main:job_template_jobs_list', args=(jt.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

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
        url = reverse('main:job_template_jobs_list', args=(jt.pk,))
        data = dict(
            name='new job from template',
            credential=self.cred_bob.pk,
        )

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url, data, methods=('post',))

        # sue can create a new job from the template.
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)

        # FIXME: Check other credentials and optional fields.

class JobTest(BaseJobTestMixin, django.test.TestCase):

    def test_get_job_list(self):
        url = reverse('main:job_list')

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

        # sue's credentials (superuser) == 200, full list
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
        qs = Job.objects.all()
        self.check_pagination_and_size(response, qs.count())
        self.check_list_ids(response, qs)

        # FIXME: Check individual job result fields.
        # FIXME: Check with other credentials.

    def test_post_job_list(self):
        url = reverse('main:job_list')
        data = dict(
            name='new job without template',
            job_type=PERM_INVENTORY_DEPLOY,
            inventory=self.inv_ops_east.pk,
            project=self.proj_prod.pk,
            playbook=self.proj_prod.playbooks[0],
            credential=self.cred_ops_east.pk,
        )

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url, data, methods=('post',))

        # sue can create a new job without a template.
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)

        # sue can also create a job here from a template.
        jt = self.jt_ops_east_run
        data = dict(
            name='new job from template',
            job_template=jt.pk,
        )
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)

        # FIXME: Check with other credentials and optional fields.

    def test_get_job_detail(self):
        job = self.job_ops_east_run
        url = reverse('main:job_detail', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

        # sue can read the job detail.
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
            self.assertEqual(response['url'], url)

        # FIXME: Check with other credentials and optional fields.

    def test_put_job_detail(self):
        job = self.job_ops_west_run
        url = reverse('main:job_detail', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url, methods=('put',))# 'patch'))

        # sue can update the job detail only if the job is new.
        self.assertEqual(job.status, 'new')
        with self.current_user(self.user_sue):
            data = self.get(url)
            data['name'] = '%s-updated' % data['name']
            response = self.put(url, data)
            #patch_data = dict(name='%s-changed' % data['name'])
            #response = self.patch(url, patch_data)

        # sue cannot update the job detail if it is in any other state.
        for status in ('pending', 'running', 'successful', 'failed', 'error',
                       'canceled'):
            job.status = status
            job.save()
            with self.current_user(self.user_sue):
                data = self.get(url)
                data['name'] = '%s-updated' % data['name']
                self.put(url, data, expect=405)
                #patch_data = dict(name='%s-changed' % data['name'])
                #self.patch(url, patch_data, expect=405)

        # FIXME: Check with other credentials and readonly fields.

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

# Need to disable transaction middleware for testing so that the callback
# management command will be able to read the database changes made to start
# the job.  It won't be an issue normally, because the task will be running
# asynchronously; the start API call will update the database, queue the task,
# then return immediately (committing the transaction) before celery has even
# woken up to run the new task.
MIDDLEWARE_CLASSES = filter(lambda x: not x.endswith('TransactionMiddleware'),
                            settings.MIDDLEWARE_CLASSES)

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   ANSIBLE_TRANSPORT='local',
                   MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES)
class JobStartCancelTest(BaseJobTestMixin, django.test.LiveServerTestCase):
    '''Job API tests that need to use the celery task backend.'''

    def setUp(self):
        super(JobStartCancelTest, self).setUp()
        settings.INTERNAL_API_URL = self.live_server_url

    def tearDown(self):
        super(JobStartCancelTest, self).tearDown()

    def test_job_start(self):
        job = self.job_ops_east_run
        url = reverse('main:job_start', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)
        self.check_invalid_auth(url, methods=('post',))

        # Sue can start a job (when passwords are already saved) as long as the
        # status is new.  Reverse list so "new" will be last.
        for status in reversed([x[0] for x in JOB_STATUS_CHOICES]):
            if status == 'waiting':
                continue
            job.status = status
            job.save()
            with self.current_user(self.user_sue):
                response = self.get(url)
                if status == 'new':
                    self.assertTrue(response['can_start'])
                    self.assertFalse(response['passwords_needed_to_start'])
                    response = self.post(url, {}, expect=202)
                    job = Job.objects.get(pk=job.pk)
                    self.assertEqual(job.status, 'successful',
                                     job.result_stdout)
                else:
                    self.assertFalse(response['can_start'])
                    response = self.post(url, {}, expect=405)

        # Test with a job that prompts for SSH and sudo passwords.
        job = self.job_sup_run
        url = reverse('main:job_start', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertTrue(response['can_start'])
            self.assertEqual(set(response['passwords_needed_to_start']),
                             set(['ssh_password', 'sudo_password']))
            data = dict()
            response = self.post(url, data, expect=400)
            data['ssh_password'] = 'sshpass'
            response = self.post(url, data, expect=400)
            data2 = dict(sudo_password='sudopass')
            response = self.post(url, data2, expect=400)
            data.update(data2)
            response = self.post(url, data, expect=202)
            job = Job.objects.get(pk=job.pk)
            # FIXME: Test run gets the following error in this case:
            #   fatal: [hostname] => sudo output closed while waiting for password prompt:
            #self.assertEqual(job.status, 'successful')

        # Test with a job that prompts for SSH unlock key, given the wrong key.
        job = self.jt_ops_west_run.create_job(
            credential=self.cred_greg,
            created_by=self.user_sue,
        )
        url = reverse('main:job_start', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertTrue(response['can_start'])
            self.assertEqual(set(response['passwords_needed_to_start']),
                             set(['ssh_key_unlock']))
            data = dict()
            response = self.post(url, data, expect=400)
            # The job should start but fail.
            data['ssh_key_unlock'] = 'sshunlock'
            response = self.post(url, data, expect=202)
            job = Job.objects.get(pk=job.pk)
            self.assertEqual(job.status, 'failed')

        # Test with a job that prompts for SSH unlock key, given the right key.
        from awx.main.tests.tasks import TEST_SSH_KEY_DATA_UNLOCK
        job = self.jt_ops_west_run.create_job(
            credential=self.cred_greg,
            created_by=self.user_sue,
        )
        url = reverse('main:job_start', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertTrue(response['can_start'])
            self.assertEqual(set(response['passwords_needed_to_start']),
                             set(['ssh_key_unlock']))
            data = dict()
            response = self.post(url, data, expect=400)
            data['ssh_key_unlock'] = TEST_SSH_KEY_DATA_UNLOCK
            response = self.post(url, data, expect=202)
            job = Job.objects.get(pk=job.pk)
            self.assertEqual(job.status, 'successful')

        # FIXME: Test with other users, test when passwords are required.

    def test_job_cancel(self):
        job = self.job_ops_east_run
        url = reverse('main:job_cancel', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)
        self.check_invalid_auth(url, methods=('post',))

        # sue can cancel the job, but only when it is pending or running.
        for status in [x[0] for x in JOB_STATUS_CHOICES]:
            if status == 'waiting':
                continue
            job.status = status
            job.save()
            with self.current_user(self.user_sue):
                response = self.get(url)
                if status in ('pending', 'running'):
                    self.assertTrue(response['can_cancel'])
                    response = self.post(url, {}, expect=202)
                else:
                    self.assertFalse(response['can_cancel'])
                    response = self.post(url, {}, expect=405)

        # FIXME: Test with other users.

    def test_get_job_results(self):
        # Start/run a job and then access its results via the API.
        job = self.job_ops_east_run
        job.start()

        # Check that the job detail has been updated.
        url = reverse('main:job_detail', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertEqual(response['status'], 'successful')
            self.assertTrue(response['result_stdout'])

        # Test job events for completed job.
        url = reverse('main:job_job_events_list', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            qs = job.job_events.all()
            self.assertTrue(qs.count())
            self.check_pagination_and_size(response, qs.count())
            self.check_list_ids(response, qs)

        # Test individual job event detail records.
        host_ids = set()
        for job_event in job.job_events.all():
            if job_event.host:
                host_ids.add(job_event.host.pk)
            url = reverse('main:job_event_detail', args=(job_event.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)

        # Also test job event list for each host.
        for host in Host.objects.filter(pk__in=host_ids):
            url = reverse('main:host_job_events_list', args=(host.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = host.job_events.all()
                self.assertTrue(qs.count())
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)

        # Test job event list for groups.
        for group in self.inv_ops_east.groups.all():
            url = reverse('main:group_job_events_list', args=(group.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = group.job_events.all()
                self.assertTrue(qs.count(), group)
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)

        # Test global job event list.
        url = reverse('main:job_event_list')
        with self.current_user(self.user_sue):
            response = self.get(url)
            qs = JobEvent.objects.all()
            self.assertTrue(qs.count())
            self.check_pagination_and_size(response, qs.count())
            self.check_list_ids(response, qs)

        # Test job host summaries for completed job.
        url = reverse('main:job_job_host_summaries_list', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            qs = job.job_host_summaries.all()
            self.assertTrue(qs.count())
            self.check_pagination_and_size(response, qs.count())
            self.check_list_ids(response, qs)
            # Every host referenced by a job_event should be present as a job
            # host summary record.
            self.assertEqual(host_ids,
                             set(qs.values_list('host__pk', flat=True)))

        # Test individual job host summary records.
        for job_host_summary in job.job_host_summaries.all():
            url = reverse('main:job_host_summary_detail',
                          args=(job_host_summary.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)

        # Test job host summaries for each host.
        for host in Host.objects.filter(pk__in=host_ids):
            url = reverse('main:host_job_host_summaries_list', args=(host.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = host.job_host_summaries.all()
                self.assertTrue(qs.count())
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)

        # Test job host summaries for groups.
        for group in self.inv_ops_east.groups.all():
            url = reverse('main:group_job_host_summaries_list', args=(group.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = group.job_host_summaries.all()
                self.assertTrue(qs.count())
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   ANSIBLE_TRANSPORT='local',
                   MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES)
class JobTemplateCallbackTest(BaseJobTestMixin, django.test.LiveServerTestCase):
    '''Job template callback tests for empheral hosts.'''

    def setUp(self):
        super(JobTemplateCallbackTest, self).setUp()
        settings.INTERNAL_API_URL = self.live_server_url
        # Monkeypatch socket module DNS lookup functions for testing.
        self._original_gethostbyaddr = socket.gethostbyaddr
        self._original_getaddrinfo = socket.getaddrinfo
        socket.gethostbyaddr = self.gethostbyaddr
        socket.getaddrinfo = self.getaddrinfo

    def tearDown(self):
        super(JobTemplateCallbackTest, self).tearDown()
        socket.gethostbyaddr = self._original_gethostbyaddr
        socket.getaddrinfo = self._original_getaddrinfo

    def atoh(self, a):
        '''Convert IP address to integer in host byte order.'''
        return socket.ntohl(struct.unpack('I', socket.inet_aton(a))[0])

    def htoa(self, n):
        '''Convert integer in host byte order to IP address.'''
        return socket.inet_ntoa(struct.pack('I', socket.htonl(n)))

    def get_test_ips_for_host(self, host):
        '''Return test IP address(es) for given test hostname.'''
        ips = []
        try:
            h = Host.objects.exclude(name__endswith='-alias').get(name=host)
            # Primary IP for host (both forward/reverse lookups work).
            val = self.atoh('127.10.0.0') + h.pk
            ips.append(self.htoa(val))
            # Secondary IP for host (both forward/reverse lookups work).
            if h.pk % 2 == 0:
                val = self.atoh('127.20.0.0') + h.pk
                ips.append(self.htoa(val))
            # Additional IP for host (only forward lookups work).
            if h.pk % 3 == 0:
                val = self.atoh('127.30.0.0') + h.pk
                ips.append(self.htoa(val))
            # Additional IP for host (neither forward/reverse lookups work).
            if h.pk % 3 == 1:
                val = self.atoh('127.40.0.0') + h.pk
                ips.append(self.htoa(val))
        except Host.DoesNotExist:
            pass
        return ips

    def get_test_host_for_ip(self, ip):
        '''Return test hostname for given test IP address.'''
        if not ip.startswith('127.10.') and not ip.startswith('127.20.'):
            return None
        val = self.atoh(ip)
        try:
            return Host.objects.get(pk=(val & 0x0ffff)).name
        except Host.DoesNotExist:
            return None

    def test_dummy_host_ip_lookup(self):
        all_ips = set()
        for host in Host.objects.all():
            ips = self.get_test_ips_for_host(host.name)
            self.assertTrue(ips)
            all_ips.update(ips)
        ips = self.get_test_ips_for_host('invalid_host_name')
        self.assertFalse(ips)
        for ip in all_ips:
            host = self.get_test_host_for_ip(ip)
            if ip.startswith('127.30.') or ip.startswith('127.40.'):
                continue
            self.assertTrue(host)
            ips = self.get_test_ips_for_host(host)
            self.assertTrue(ip in ips)
        host = self.get_test_host_for_ip('127.10.254.254')
        self.assertFalse(host)

    def gethostbyaddr(self, ip):
        if not ip.startswith('127.'):
            return self._original_gethostbyaddr(ip)
        host = self.get_test_host_for_ip(ip)
        if not host:
            raise socket.herror('unknown test host')
        raddr = '.'.join(list(reversed(ip.split('.'))) + ['in-addr', 'arpa'])
        return (host, [raddr], [ip])
         
    def getaddrinfo(self, host, port, family=0, socktype=0, proto=0, flags=0):
        if family or socktype or proto or flags:
            return self._original_getaddrinfo(host, port, family, socktype,
                                              proto, flags)
        port = port or 0
        try:
            socket.inet_aton(host)
            addrs = [host]
        except socket.error:
            addrs = self.get_test_ips_for_host(host)
            addrs = [x for x in addrs if not x.startswith('127.40.')]
        if not addrs:
            raise socket.gaierror('test host not found')
        results = []
        for addr in addrs:
            results.append((socket.AF_INET, socket.SOCK_STREAM,
                            socket.IPPROTO_TCP, '', (addr, port)))
            results.append((socket.AF_INET, socket.SOCK_DGRAM,
                            socket.IPPROTO_UDP, '', (addr, port)))
        return results

    def test_job_template_callback(self):
        # Set ansible_ssh_host for certain hosts, update name to be an alias.
        for host in Host.objects.all():
            ips = self.get_test_ips_for_host(host.name)
            for ip in ips:
                if ip.startswith('127.40.'):
                    host.name = '%s-alias' % host.name
                    host_vars = host.variables_dict
                    host_vars['ansible_ssh_host'] = ip
                    host.variables = json.dumps(host_vars)
                    host.save()
        
        # Find a valid job template to use to test the callback.
        job_template = None
        qs = JobTemplate.objects.filter(job_type='run',
                                        credential__isnull=False)
        qs = qs.exclude(host_config_key='')
        for jt in qs:
            if not jt.can_start_without_user_input():
                continue
            job_template = jt
            break
        self.assertTrue(job_template)
        url = reverse('main:job_template_callback', args=(job_template.pk,))
        data = dict(host_config_key=job_template.host_config_key)

        # Test a POST to start a new job.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        host = host_qs[0]
        host_ip = self.get_test_ips_for_host(host.name)[0]
        jobs_qs = job_template.jobs.filter(launch_type='callback').order_by('-pk')
        self.assertEqual(jobs_qs.count(), 0)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 1)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # GET as unauthenticated user will prompt for authentication.
        self.get(url, expect=401, remote_addr=host_ip)

        # Test GET (as super user) to validate host.
        with self.current_user(self.user_sue):
            response = self.get(url, expect=200, remote_addr=host_ip)
            self.assertEqual(response['host_config_key'],
                             job_template.host_config_key)
            self.assertEqual(response['matching_hosts'], [host.name])

        # POST but leave out the host_config_key.
        self.post(url, {}, expect=403, remote_addr=host_ip)

        # Try with REMOTE_ADDR empty.
        self.post(url, data, expect=400, remote_addr='')

        # Try with REMOTE_ADDR set to an unknown address.
        self.post(url, data, expect=400, remote_addr='127.127.0.1')

        # Try using an alternate IP for the host (but one that also resolves
        # via reverse lookup).
        host = None
        host_ip = None
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        for h in host_qs:
            ips = self.get_test_ips_for_host(h.name)
            for ip in ips:
                if ip.startswith('127.20.'):
                    host = h
                    host_ip = ip
                    break
            if host_ip:
                break
        self.assertTrue(host)
        self.assertEqual(jobs_qs.count(), 1)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 2)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # Try using an IP for the host that doesn't resolve via reverse lookup,
        # but can be found by doing a forward lookup on the host name.
        host = None
        host_ip = None
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        for h in host_qs:
            ips = self.get_test_ips_for_host(h.name)
            for ip in ips:
                if ip.startswith('127.30.'):
                    host = h
                    host_ip = ip
                    break
            if host_ip:
                break
        self.assertTrue(host)
        self.assertEqual(jobs_qs.count(), 2)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 3)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # Try using address only specified via ansible_ssh_host.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.filter(variables__icontains='ansible_ssh_host')
        host = host_qs[0]
        host_ip = host.variables_dict['ansible_ssh_host']
        self.assertEqual(jobs_qs.count(), 3)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 4)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # Try when hostname is also an IP address, even if a different one is
        # specified via ansible_ssh_host.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        host = None
        host_ip = None
        for h in host_qs:
            ips = self.get_test_ips_for_host(h.name)
            if len(ips) > 1:
                host = h
                host.name = list(ips)[0]
                host_vars = host.variables_dict
                host_vars['ansible_ssh_host'] = list(ips)[1]
                host.variables = json.dumps(host_vars)
                host.save()
                host_ip = list(ips)[0]
                break
        self.assertTrue(host)
        self.assertEqual(jobs_qs.count(), 4)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 5)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # Find a new job template to use.
        job_template = None
        qs = JobTemplate.objects.filter(job_type='check',
                                        credential__isnull=False)
        qs = qs.exclude(host_config_key='')
        for jt in qs:
            if not jt.can_start_without_user_input():
                continue
            job_template = jt
            break
        self.assertTrue(job_template)
        url = reverse('main:job_template_callback', args=(job_template.pk,))
        data = dict(host_config_key=job_template.host_config_key)

        # Should get an error when multiple hosts match to the same IP.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(name__endswith='-alias')
        for host in host_qs:
            host_vars = host.variables_dict
            host_vars['ansible_ssh_host'] = '127.50.0.1'
            host.variables = json.dumps(host_vars)
            host.save()
        host = host_qs[0]
        host_ip = host.variables_dict['ansible_ssh_host']
        self.post(url, data, expect=400, remote_addr=host_ip)

        # Find a job template to run that doesn't have a credential.
        job_template = None
        qs = JobTemplate.objects.filter(job_type='run',
                                        credential__isnull=True)
        qs = qs.exclude(host_config_key='')
        for jt in qs:
            job_template = jt
            break
        self.assertTrue(job_template)
        url = reverse('main:job_template_callback', args=(job_template.pk,))
        data = dict(host_config_key=job_template.host_config_key)

        # Test POST to start a new job when the template has no credential.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        host = host_qs[0]
        host_ip = self.get_test_ips_for_host(host.name)[0]
        self.post(url, data, expect=400, remote_addr=host_ip)

        # Find a job template to run that has a credential but would require
        # user input.
        job_template = None
        qs = JobTemplate.objects.filter(job_type='run',
                                        credential__isnull=False)
        qs = qs.exclude(host_config_key='')
        for jt in qs:
            if jt.can_start_without_user_input():
                continue
            job_template = jt
            break
        self.assertTrue(job_template)
        url = reverse('main:job_template_callback', args=(job_template.pk,))
        data = dict(host_config_key=job_template.host_config_key)

        # Test POST to start a new job when the credential would require user
        # input.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        host = host_qs[0]
        host_ip = self.get_test_ips_for_host(host.name)[0]
        self.post(url, data, expect=400, remote_addr=host_ip)
