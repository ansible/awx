# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import contextlib
import json
import socket
import struct
import threading
import time
import urlparse

# Django
import django.test
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.encoding import smart_str

# Requests
import requests

# AWX
from awx.main.models import * # noqa
from base import BaseJobTestMixin

__all__ = ['JobTemplateTest', 'JobTest', 'JobTemplateCallbackTest', 'JobTransactionTest', 'JobTemplateSurveyTest']

TEST_ASYNC_PLAYBOOK = '''
- hosts: all
  gather_facts: false
  tasks:
  - name: async task should pass
    command: sleep 10
    async: 20
    poll: 1
'''

TEST_SIMPLE_REQUIRED_SURVEY = '''
{
    "name": "Simple",
    "description": "Description",
    "spec": [
        {
        "type": "text",
        "question_name": "favorite color",
        "question_description": "What is your favorite color?",
        "variable": "favorite_color",
        "choices": "",
        "min": "",
        "max": "",
        "required": true,
        "default": "blue"
        }
    ]
}
'''

TEST_SIMPLE_NONREQUIRED_SURVEY = '''
{
    "name": "Simple",
    "description": "Description",
    "spec": [
        {
        "type": "text",
        "question_name": "unladen swallow",
        "question_description": "What is the airspeed velocity of an unladen swallow?",
        "variable": "unladen_swallow",
        "choices": "",
        "min": "",
        "max": "",
        "required": false,
        "default": "european"
        }
    ]
}
'''

TEST_SURVEY_REQUIREMENTS = '''
{
    "name": "Simple",
    "description": "Description",
    "spec": [
        {
        "type": "text",
        "question_name": "cantbeshort",
        "question_description": "What is a long answer",
        "variable": "long_answer",
        "choices": "",
        "min": 5,
        "max": "",
        "required": false,
        "default": "yes"
        },
        {
        "type": "text",
        "question_name": "cantbelong",
        "question_description": "What is a short answer",
        "variable": "short_answer",
        "choices": "",
        "min": "",
        "max": 5,
        "required": false,
        "default": "yes"
        },
        {
        "type": "text",
        "question_name": "reqd",
        "question_description": "I should be required",
        "variable": "reqd_answer",
        "choices": "",
        "min": "",
        "max": "",
        "required": true,
        "default": "yes"
        },
        {
        "type": "multiplechoice",
        "question_name": "achoice",
        "question_description": "Need one of these",
        "variable": "single_choice",
        "choices": ["one", "two"],
        "min": "",
        "max": "",
        "required": false,
        "default": "yes"
        },
        {
        "type": "multiselect",
        "question_name": "mchoice",
        "question_description": "Can have multiples of these",
        "variable": "multi_choice",
        "choices": ["one", "two", "three"],
        "min": "",
        "max": "",
        "required": false,
        "default": "yes"
        },
        {
        "type": "integer",
        "question_name": "integerchoice",
        "question_description": "I need an int here",
        "variable": "int_answer",
        "choices": "",
        "min": 1,
        "max": 5,
        "required": false,
        "default": ""
        },
        {
        "type": "integer",
        "question_name": "integerchoicewithoutmax",
        "question_description": "I need an int here without max",
        "variable": "int_answer_no_max",
        "choices": "",
        "min": 1,
        "required": false,
        "default": ""
        },
        {
        "type": "float",
        "question_name": "float",
        "question_description": "I need a float here",
        "variable": "float_answer",
        "choices": "",
        "min": 2,
        "max": 5,
        "required": false,
        "default": ""
        },
        {
        "type": "json",
        "question_name": "jsonanswer",
        "question_description": "This answer should validate as json",
        "variable": "json_answer",
        "choices": "",
        "min": "",
        "max": "",
        "required": false,
        "default": ""
        }
    ]
}
'''

class JobTemplateTest(BaseJobTestMixin, django.test.TestCase):

    JOB_TEMPLATE_FIELDS = ('id', 'type', 'url', 'related', 'summary_fields',
                           'created', 'modified', 'name', 'description',
                           'job_type', 'inventory', 'project', 'playbook',
                           'become_enabled', 'credential',
                           'cloud_credential', 'force_handlers', 'forks',
                           'limit', 'verbosity', 'extra_vars',
                           'ask_variables_on_launch', 'job_tags', 'skip_tags',
                           'start_at_task', 'host_config_key', 'status',
                           'next_job_run', 'has_schedules', 'last_job_run',
                           'last_job_failed', 'survey_enabled')

    def test_get_job_template_list(self):
        url = reverse('api:job_template_list')
        qs = JobTemplate.objects.distinct()
        fields = self.JOB_TEMPLATE_FIELDS

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

        # Sue's credentials (superuser) == 200, full list
        self.check_get_list(url, self.user_sue, qs, fields)

        # Alex's credentials (admin of all orgs) == 200, full list
        self.check_get_list(url, self.user_alex, qs, fields)

        # # Bob is an admin for Eng he can see all Engineering templates
        # this is: 2 Engineering templates and 1 Support Template
        # Note: He is able to see the scan job from the support organization possibly incorrect
        #       due to being an org admin for that project and no credential assigned to that template
        with self.current_user(self.user_bob):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 3)
            
        # Chuck has permission to see all Eng Job Templates as Lead Engineer
        # Note: Since chuck is an org admin he can also see the support scan template
        with self.current_user(self.user_chuck):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 3)

        # Doug is in engineering but can only run scan jobs so he can only see the one Job Template
        with self.current_user(self.user_doug):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 1)

        # Juan can't see any job templates in Engineering because he lacks the inventory read permission
        with self.current_user(self.user_juan):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 0)

        # We give Juan inventory permission and he can see both Job Templates because he already has deploy permission
        # Now he can see both job templates
        Permission.objects.create(
            inventory       = self.inv_eng,
            user            = self.user_juan,
            permission_type = PERM_INVENTORY_READ,
            created_by      = self.user_sue
        )
        with self.current_user(self.user_juan):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 2)

        # Randall is on the ops testers team that has permission to run a single check playbook on ops west
        with self.current_user(self.user_randall):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 1)

        # Holly is on the ops east team and can see all of that team's job templates
        with self.current_user(self.user_holly):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 3)

        # Chuck is temporarily assigned to ops east team to help them running some playbooks
        # even though he's in a different group and org entirely he'll now see their job templates
        self.team_ops_east.users.add(self.user_chuck)
        with self.current_user(self.user_chuck):
            resp = self.get(url, expect=200)
            print [x['name'] for x in resp['results']]
            self.assertEquals(resp['count'], 6)
        

    def test_credentials_list(self):
        url = reverse('api:credential_list')
        # Greg can't see the 'south' credential because the 'southerns' team is inactive
        with self.current_user(self.user_greg):
            all_credentials = self.get(url, expect=200)
            self.assertFalse('south' in [x['username'] for x in all_credentials['results']])

        url2 = reverse('api:team_detail', args=(self.team_ops_north.id,))
        # Sue shouldn't be able to see the north credential once deleting its team
        with self.current_user(self.user_sue):
            self.delete(url2, expect=204)
            all_credentials = self.get(url, expect=200)
            self.assertFalse('north' in [x['username'] for x in all_credentials['results']])

    def test_post_job_template_list(self):
        url = reverse('api:job_template_list')
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
            detail_url = reverse('api:job_template_detail',
                                 args=(response['id'],))
            self.assertEquals(response['url'], detail_url)

        # Check that all fields provided were set.
        jt = JobTemplate.objects.get(pk=response['id'])
        self.assertEqual(jt.name, data['name'])
        self.assertEqual(jt.job_type, data['job_type'])
        self.assertEqual(jt.inventory.pk, data['inventory'])
        self.assertEqual(jt.credential, None)
        self.assertEqual(jt.project.pk, data['project'])
        self.assertEqual(smart_str(jt.playbook), data['playbook'])

        # Test that all required fields are really required.
        data['name'] = 'another new job template'
        for field in ('name', 'inventory', 'project', 'playbook'):
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

        # Test unique constraint on names.
        with self.current_user(self.user_sue):
            d = dict(data.items())
            d['name'] = 'new job template'
            response = self.post(url, d, expect=400)
            self.assertTrue('name' in response)
            self.assertTrue('Job template with this Name already exists.' in response['name'])
            self.assertTrue('__all__' not in response)

        data = dict(
            name      = 'ops job template',
            job_type  = PERM_INVENTORY_DEPLOY,
            inventory = self.inv_ops_west.pk,
            project   = self.proj_prod.pk,
            playbook  = self.proj_prod.playbooks[0],
        )

        # randall can't create a job template since his job is to check templates
        # as per the ops testers team permission
        with self.current_user(self.user_randall):
            response = self.post(url, data, expect=403)

        # greg can because he is the head of operations
        with self.current_user(self.user_greg):
            response = self.post(url, data, expect=201)

        data = dict(
            name      = 'eng job template',
            job_type  = PERM_INVENTORY_DEPLOY,
            inventory = self.inv_eng.pk,
            project   = self.proj_dev.pk,
            playbook  = self.proj_dev.playbooks[0],
        )

        # Neither Juan or Doug can create job templates as they have Permissions
        # that only allow them to DEPLOY and CHECK respectively
        with self.current_user(self.user_juan):
            response = self.post(url, data, expect=403)

        with self.current_user(self.user_doug):
            response = self.post(url, data, expect=403)

        # Hannibal, despite his questionable social habits has a user Permission
        # that allows him to create playbooks
        with self.current_user(self.user_hannibal):
            response = self.post(url, data, expect=201)

        # FIXME: Check other credentials and optional fields.

    def test_get_job_template_detail(self):
        jt = self.jt_eng_run
        url = reverse('api:job_template_detail', args=(jt.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

        # sue can read the job template detail.
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
            self.assertEqual(response['url'], url)
            self.assertEqual(response['cloud_credential'], None)

        # FIXME: Check other credentials and optional fields.

        # TODO: add more tests that show
        # the method used to START a JobTemplate follow the exact same permissions as those to create it ...
        # and that jobs come back nicely serialized with related resources and so on ...
        # that we can drill all the way down and can get at host failure lists, etc ...

    def test_put_job_template_detail(self):
        jt = self.jt_eng_run
        url = reverse('api:job_template_detail', args=(jt.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url, methods=('put',))# 'patch'))

        # sue can update the job template detail.
        with self.current_user(self.user_sue):
            data = self.get(url)
            data['name'] = '%s-updated' % data['name']
            self.put(url, data)

        # FIXME: Check other credentials and optional fields.

    def test_get_job_template_job_list(self):
        jt = self.jt_eng_run
        url = reverse('api:job_template_jobs_list', args=(jt.pk,))

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
        url = reverse('api:job_template_jobs_list', args=(jt.pk,))
        data = dict(
            credential=self.cred_bob.pk,
        )

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url, data, methods=('post',))

        # sue can create a new job from the template.
        with self.current_user(self.user_sue):
            self.post(url, data, expect=201)

        # FIXME: Check other credentials and optional fields.

    def test_post_scan_job_template(self):
        url = reverse('api:job_template_list')
        data = dict(
            name = 'scan job template 1',
            job_type = PERM_INVENTORY_SCAN,
            inventory = self.inv_eng.pk,
        )
        self.create_test_license_file(features=dict(system_tracking=False))
        # Without the system tracking license feature even super users can't create scan jobs
        with self.current_user(self.user_sue):
            data['credential'] = self.cred_sue.pk
            response = self.post(url, data, expect=402)
        self.create_test_license_file(features=dict(system_tracking=True))
        # Scan Jobs can not be created with survey enabled
        with self.current_user(self.user_sue):
            data['credential'] = self.cred_sue.pk
            data['survey_enabled'] = True
            response = self.post(url, data, expect=400)
            data.pop("survey_enabled")
        # Regular users, even those who have access to the inv and cred can't create scan jobs templates
        with self.current_user(self.user_doug):
            data['credential'] = self.cred_doug.pk
            response = self.post(url, data, expect=403)
        # Org admins can create scan job templates in their org
        with self.current_user(self.user_chuck):
            data['credential'] = self.cred_chuck.pk
            response = self.post(url, data, expect=201)
            detail_url = reverse('api:job_template_detail',
                                 args=(response['id'],))
        # Non Org Admins don't have permission to access it though
        with self.current_user(self.user_doug):
            self.get(detail_url, expect=403)

class JobTest(BaseJobTestMixin, django.test.TestCase):

    def test_get_job_list(self):
        url = reverse('api:job_list')

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
        url = reverse('api:job_list')
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
            self.post(url, data, expect=201)

        # alex can't create a job without a template, only super users can do that
        with self.current_user(self.user_alex):
            self.post(url, data, expect=403)

        # sue can also create a job here from a template.
        jt = self.jt_ops_east_run
        data = dict(
            name='new job from template',
            job_template=jt.pk,
        )
        with self.current_user(self.user_sue):
            self.post(url, data, expect=201)

        # sue can't create a job when it is hidden due to inactive team

        # FIXME: Check with other credentials and optional fields.

    def test_get_job_detail(self):
        #job = self.job_ops_east_run
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'success')
        url = reverse('api:job_detail', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)

        # sue can read the job detail.
        with self.current_user(self.user_sue):
            self.options(url)
            self.head(url)
            response = self.get(url)
            self.assertEqual(response['url'], url)
            self.assertEqual(response['cloud_credential'], None)

        # FIXME: Check with other credentials and optional fields.

    def test_put_job_detail(self):
        #job = self.job_ops_west_run
        job = self.make_job(self.jt_ops_west_run, self.user_sue, 'success')
        url = reverse('api:job_detail', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url, methods=('put',))# 'patch'))

        # sue can update the job detail only if the job is new.
        job.status = 'new'
        job.save()
        self.assertEqual(job.status, 'new')
        with self.current_user(self.user_sue):
            data = self.get(url)
            data['limit'] = '%s-updated' % data['limit']
            self.put(url, data)

        # sue cannot update the job detail if it is in any other state.
        for status in ('pending', 'running', 'successful', 'failed', 'error',
                       'canceled'):
            job.status = status
            job.save()
            with self.current_user(self.user_sue):
                data = self.get(url)
                data['limit'] = '%s-updated' % data['limit']
                self.put(url, data, expect=405)
                #patch_data = dict(limit='%s-changed' % data['limit'])
                #self.patch(url, patch_data, expect=405)

        # FIXME: Check with other credentials and readonly fields.

    def _test_mainline(self):
        url = reverse('api:job_list')

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

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   ANSIBLE_TRANSPORT='local')
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
        url = reverse('api:job_template_callback', args=(job_template.pk,))
        data = dict(host_config_key=job_template.host_config_key)

        # Test a POST to start a new job.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        host = host_qs[0]
        host_ip = self.get_test_ips_for_host(host.name)[0]
        jobs_qs = job_template.jobs.filter(launch_type='callback').order_by('-pk')
        self.assertEqual(jobs_qs.count(), 0)

        # Create the job itself.
        result = self.post(url, data, expect=202, remote_addr=host_ip)

        # Establish that we got back what we expect, and made the changes
        # that we expect.
        self.assertTrue('Location' in result.response, result.response)
        self.assertEqual(jobs_qs.count(), 1)
        job = jobs_qs[0]
        self.assertEqual(urlparse.urlsplit(result.response['Location']).path,
                         job.get_absolute_url())
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # Run the callback job again with extra vars and verify their presence
        data.update(dict(extra_vars=dict(key="value")))
        result = self.post(url, data, expect=202, remote_addr=host_ip)
        jobs_qs = job_template.jobs.filter(launch_type='callback').order_by('-pk')
        job = jobs_qs[0]
        self.assertTrue("key" in job.extra_vars)

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

        # Create a pending job that will block creation of another job
        j = job_template.create_job(limit=job.limit, launch_type='callback')
        j.status = 'pending'
        j.save()
        # This should fail since there is already a pending/waiting callback job on that job template involving that host
        self.post(url, data, expect=400, remote_addr=host_ip)
        j.delete() # Remove that so it's not hanging around

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
        self.assertEqual(jobs_qs.count(), 2)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 3)
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
        self.assertEqual(jobs_qs.count(), 3)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 4)
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
        self.assertEqual(jobs_qs.count(), 4)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 5)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, host.name)
        self.assertEqual(job.hosts.count(), 1)
        self.assertEqual(job.hosts.all()[0], host)

        # Set a limit on the job template to verify the callback job limit is
        # set to the intersection of this limit and the host name.
        job_template.limit = 'bakers:slicers:packagers'
        job_template.save(update_fields=['limit'])

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
        self.assertEqual(jobs_qs.count(), 5)
        self.post(url, data, expect=202, remote_addr=host_ip)
        self.assertEqual(jobs_qs.count(), 6)
        job = jobs_qs[0]
        self.assertEqual(job.launch_type, 'callback')
        self.assertEqual(job.limit, ':&'.join([job_template.limit, host.name]))
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
        url = reverse('api:job_template_callback', args=(job_template.pk,))
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
        url = reverse('api:job_template_callback', args=(job_template.pk,))
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
        url = reverse('api:job_template_callback', args=(job_template.pk,))
        data = dict(host_config_key=job_template.host_config_key)

        # Test POST to start a new job when the credential would require user
        # input.
        host_qs = job_template.inventory.hosts.order_by('pk')
        host_qs = host_qs.exclude(variables__icontains='ansible_ssh_host')
        host = host_qs[0]
        host_ip = self.get_test_ips_for_host(host.name)[0]
        self.post(url, data, expect=400, remote_addr=host_ip)


@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   ANSIBLE_TRANSPORT='local')
class JobTransactionTest(BaseJobTestMixin, django.test.LiveServerTestCase):
    '''Job test of transaction locking using the celery task backend.'''

    def setUp(self):
        super(JobTransactionTest, self).setUp()
        settings.INTERNAL_API_URL = self.live_server_url

    def tearDown(self):
        super(JobTransactionTest, self).tearDown()

    def _job_detail_polling_thread(self, url, auth, errors):
        time.sleep(1)
        while True:
            time.sleep(0.1)
            try:
                response = requests.get(url, auth=auth)
                response.raise_for_status()
                data = json.loads(response.content)
                if data.get('status', '') not in ('new', 'pending', 'running'):
                    break
            except Exception, e:
                errors.append(e)
                break

    @contextlib.contextmanager
    def poll_job_detail(self, url, auth, errors):
        try:
            t = threading.Thread(target=self._job_detail_polling_thread,
                                 args=(url, auth, errors))
            t.start()
            yield
        finally:
            t.join(20)

    def test_for_job_deadlocks(self):
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.skipTest('Not using PostgreSQL')
        # Create lots of extra test hosts to trigger job event callbacks
        #job = self.job_eng_run
        job = self.make_job(self.jt_eng_run, self.user_sue, 'new')
        inv = job.inventory
        for x in xrange(50):
            h = inv.hosts.create(name='local-%d' % x)
            for g in inv.groups.all():
                g.hosts.add(h)

        job_detail_url = reverse('api:job_detail', args=(job.pk,))
        job_detail_url = urlparse.urljoin(self.live_server_url, job_detail_url)
        auth = ('sue', self._user_passwords['sue'])
        errors = []
        with self.poll_job_detail(job_detail_url, auth, errors):
            with self.current_user(self.user_sue):
                url = reverse('api:job_start', args=(job.pk,))
                response = self.get(url)
                self.assertTrue(response['can_start'])
                self.assertFalse(response['passwords_needed_to_start'])
                response = self.post(url, {}, expect=202)
                job = Job.objects.get(pk=job.pk)
                self.assertEqual(job.status, 'successful', job.result_stdout)
        self.assertFalse(errors)

class JobTemplateSurveyTest(BaseJobTestMixin, django.test.TestCase):
    def setUp(self):
        super(JobTemplateSurveyTest, self).setUp()
        # TODO: Test non-enterprise license
        self.create_test_license_file()

    def tearDown(self):
        super(JobTemplateSurveyTest, self).tearDown()

    def test_post_patch_job_template_survey_wrong_license(self):
        url = reverse('api:job_template_list')
        data = dict(
            name         = 'launched job template',
            job_type     = PERM_INVENTORY_DEPLOY,
            inventory    = self.inv_eng.pk,
            project      = self.proj_dev.pk,
            playbook     = self.proj_dev.playbooks[0],
            credential   = self.cred_sue.pk,
            survey_enabled = True,
        )
        self.create_test_license_file(features=dict(surveys=False))
        with self.current_user(self.user_sue):
            self.post(url, data, expect=402)
        data['survey_enabled'] = False
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)
        jt_url = reverse('api:job_template_detail', args=(response['id'],))
        with self.current_user(self.user_sue):
            self.patch(jt_url, dict(survey_enabled=True), expect=402)
        
    def test_post_job_template_survey(self):
        url = reverse('api:job_template_list')
        data = dict(
            name         = 'launched job template',
            job_type     = PERM_INVENTORY_DEPLOY,
            inventory    = self.inv_eng.pk,
            project      = self.proj_dev.pk,
            playbook     = self.proj_dev.playbooks[0],
            credential   = self.cred_sue.pk,
            survey_enabled = True,
        )
        with self.current_user(self.user_sue):
            response = self.post(url, data, expect=201)
            new_jt_id = response['id']
            detail_url = reverse('api:job_template_detail',
                                 args=(new_jt_id,))
            self.assertEquals(response['url'], detail_url)
        url = reverse('api:job_template_survey_spec', args=(new_jt_id,))
        launch_url = reverse('api:job_template_launch', args=(new_jt_id,))
        with self.current_user(self.user_sue):
            # If no survey spec is available, survey_enabled on launch endpoint
            # should return, and should be able to launch template without error.
            response = self.get(launch_url)
            self.assertFalse(response['survey_enabled'])
            self.post(launch_url, {}, expect=202)
            # Now post a survey spec and check that the answer is set in the
            # job's extra vars.
            self.post(url, json.loads(TEST_SIMPLE_REQUIRED_SURVEY), expect=200)
            response = self.get(launch_url)
            self.assertTrue(response['survey_enabled'])
            self.assertTrue('favorite_color' in response['variables_needed_to_start'])
            response = self.post(launch_url, dict(extra_vars=dict(favorite_color="green")), expect=202)
            job = Job.objects.get(pk=response["job"])
            job_extra = json.loads(job.extra_vars)
            self.assertTrue("favorite_color" in job_extra)

        # launch job template with required survey without providing survey data
        with self.current_user(self.user_sue):
            self.post(url, json.loads(TEST_SIMPLE_REQUIRED_SURVEY), expect=200)
            response = self.get(launch_url)
            self.assertTrue('favorite_color' in response['variables_needed_to_start'])
            response = self.post(launch_url, dict(extra_vars=dict()), expect=400)
            # Note: The below assertion relies on how survey_variable_validation() crafts
            # the error message
            self.assertIn("'favorite_color' value missing", response['variables_needed_to_start'])

        # launch job template with required survey without providing survey data and without
        # even providing extra_vars
        with self.current_user(self.user_sue):
            self.post(url, json.loads(TEST_SIMPLE_REQUIRED_SURVEY), expect=200)
            response = self.get(launch_url)
            self.assertTrue('favorite_color' in response['variables_needed_to_start'])
            response = self.post(launch_url, {}, expect=400)
            # Note: The below assertion relies on how survey_variable_validation() crafts
            # the error message
            self.assertIn("'favorite_color' value missing", response['variables_needed_to_start'])

        with self.current_user(self.user_sue):
            response = self.post(url, json.loads(TEST_SIMPLE_NONREQUIRED_SURVEY), expect=200)
            response = self.get(launch_url)
            self.assertTrue(len(response['variables_needed_to_start']) == 0)

        with self.current_user(self.user_sue):
            response = self.post(url, json.loads(TEST_SURVEY_REQUIREMENTS), expect=200)
            # Just the required answer should work
            self.post(launch_url, dict(extra_vars=dict(reqd_answer="foo")), expect=202)
            # Short answer but requires a long answer
            self.post(launch_url, dict(extra_vars=dict(long_answer='a', reqd_answer="foo")), expect=400)
            # Long answer but requires a short answer
            self.post(launch_url, dict(extra_vars=dict(short_answer='thisissomelongtext', reqd_answer="foo")), expect=400)
            # Long answer but missing required answer
            self.post(launch_url, dict(extra_vars=dict(long_answer='thisissomelongtext')), expect=400)
            # Integer that's not big enough
            self.post(launch_url, dict(extra_vars=dict(int_answer=0, reqd_answer="foo")), expect=400)
            # Integer that's too big
            self.post(launch_url, dict(extra_vars=dict(int_answer=10, reqd_answer="foo")), expect=400)
            # Integer that's just riiiiight
            self.post(launch_url, dict(extra_vars=dict(int_answer=3, reqd_answer="foo")), expect=202)
            # Integer bigger than min with no max defined
            self.post(launch_url, dict(extra_vars=dict(int_answer_no_max=3, reqd_answer="foo")), expect=202)
            # Integer answer that's the wrong type
            self.post(launch_url, dict(extra_vars=dict(int_answer="test", reqd_answer="foo")), expect=400)
            # Float that's too big
            self.post(launch_url, dict(extra_vars=dict(float_answer=10.5, reqd_answer="foo")), expect=400)
            # Float that's too small
            self.post(launch_url, dict(extra_vars=dict(float_answer=1.995, reqd_answer="foo")), expect=400)
            # float that's just riiiiight
            self.post(launch_url, dict(extra_vars=dict(float_answer=2.01, reqd_answer="foo")), expect=202)
            # float answer that's the wrong type
            self.post(launch_url, dict(extra_vars=dict(float_answer="test", reqd_answer="foo")), expect=400)
            # Wrong choice in single choice
            self.post(launch_url, dict(extra_vars=dict(reqd_answer="foo", single_choice="three")), expect=400)
            # Wrong choice in multi choice
            self.post(launch_url, dict(extra_vars=dict(reqd_answer="foo", multi_choice=["four"])), expect=400)
            # Wrong type for multi choicen
            self.post(launch_url, dict(extra_vars=dict(reqd_answer="foo", multi_choice="two")), expect=400)
            # Right choice in single choice
            self.post(launch_url, dict(extra_vars=dict(reqd_answer="foo", single_choice="two")), expect=202)
            # Right choices in multi choice
            self.post(launch_url, dict(extra_vars=dict(reqd_answer="foo", multi_choice=["one", "two"])), expect=202)
            # Nested json
            self.post(launch_url, dict(extra_vars=dict(json_answer=dict(test="val", num=1), reqd_answer="foo")), expect=202)

        # Bob can access and update the survey because he's an org-admin
        with self.current_user(self.user_bob):
            self.post(url, json.loads(TEST_SURVEY_REQUIREMENTS), expect=200)

        # Chuck is the lead engineer and has the right permissions to edit it also
        with self.current_user(self.user_chuck):
            self.post(url, json.loads(TEST_SURVEY_REQUIREMENTS), expect=200)

        # Doug shouldn't be able to access this playbook
        with self.current_user(self.user_doug):
            self.post(url, json.loads(TEST_SURVEY_REQUIREMENTS), expect=403)

        # Neither can juan because he doesn't have the job template create permission
        with self.current_user(self.user_juan):
            self.post(url, json.loads(TEST_SURVEY_REQUIREMENTS), expect=403)

        # Bob and chuck can read the template
        with self.current_user(self.user_bob):
            self.get(url, expect=200)

        with self.current_user(self.user_chuck):
            self.get(url, expect=200)    

        # Doug and Juan can't
        with self.current_user(self.user_doug):
            self.get(url, expect=403)
            
        with self.current_user(self.user_juan):
            self.get(url, expect=403)    
