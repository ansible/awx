# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
from distutils.version import StrictVersion as Version
import os
import shutil
import tempfile

# Django
from django.conf import settings
from django.test.utils import override_settings
from django.utils.timezone import now

# Django-CRUM
from crum import impersonate

# AWX
from awx.main.models import *
from awx.main.tests.base import BaseLiveServerTest
from awx.main.tasks import RunJob

TEST_PLAYBOOK = u'''
- name: test success
  hosts: test-group
  gather_facts: False
  tasks:
  - name: should pass \u2623
    command: test 1 = 1
  - name: should also pass
    command: test 2 = 2
'''

TEST_PLAYBOOK2 = '''- name: test failed
  hosts: test-group
  gather_facts: False
  tasks:
  - name: should fail
    command: test 1 = 0
'''

TEST_EXTRA_VARS_PLAYBOOK = '''
- name: test extra vars
  hosts: test-group
  gather_facts: false
  tasks:
  - fail: msg="{{item}} is not defined"
    when: "{{item}} is not defined"
    with_items:
    - tower_job_id
    - tower_job_launch_type
    - tower_job_template_id
    - tower_job_template_name
    - tower_user_id
    - tower_user_name
'''

TEST_ENV_PLAYBOOK = '''
- name: test env vars
  hosts: test-group
  gather_facts: False
  tasks:
  - shell: 'test -n "${%(env_var1)s}"'
  - shell: 'test -n "${%(env_var2)s}"'
'''

TEST_IGNORE_ERRORS_PLAYBOOK = '''
- name: test ignore errors
  hosts: test-group
  gather_facts: False
  tasks:
  - name: should fail
    command: test 1 = 0
    ignore_errors: true
'''

TEST_ASYNC_OK_PLAYBOOK = '''
- name: test async ok
  hosts: test-group
  gather_facts: false
  tasks:
  - debug: msg="one task before async"
  - name: async task should pass
    command: sleep 4
    async: 16
    poll: 1
'''

TEST_ASYNC_FAIL_PLAYBOOK = '''
- name: test async fail
  hosts: test-group
  gather_facts: false
  tasks:
  - debug: msg="one task before async"
  - name: async task should fail
    shell: sleep 4; test 1 = 0
    async: 16
    poll: 1
'''

TEST_ASYNC_TIMEOUT_PLAYBOOK = '''
- name: test async timeout
  hosts: test-group
  gather_facts: false
  tasks:
  - debug: msg="one task before async"
  - name: async task should timeout
    command: sleep 16
    async: 8
    poll: 1
'''

TEST_ASYNC_NOWAIT_PLAYBOOK = '''
- name: test async no wait
  hosts: test-group
  gather_facts: false
  tasks:
  - name: async task should run in background
    command: sleep 4
    async: 8
    poll: 0
'''

TEST_PLAYBOOK_WITH_ROLES = '''
- name: test with roles
  hosts: test-group
  gather_facts: false
  roles:
  - some_stuff
  - more_stuff
  - {role: stuff, tags: stuff}
'''

TEST_ROLE_PLAYBOOK = '''
- name: some task in a role
  command: test 1 = 1
'''

TEST_ROLE_PLAYBOOKS = {
    'some_stuff': TEST_ROLE_PLAYBOOK,
    'more_stuff': TEST_ROLE_PLAYBOOK,
    'stuff': TEST_ROLE_PLAYBOOK,
}

TEST_VAULT_PLAYBOOK = '''$ANSIBLE_VAULT;1.1;AES256
35623233333035633365383330323835353564346534363762366465316263363463396162656432
6562643539396330616265616532656466353639303338650a313466333663646431646663333739
32623935316439343636633462373633653039646336376361386439386661366434333830383634
6266613530626633390a363532373562353262323863343830343865303663306335643430396239
63393963623537326366663332656132653465646332343234656237316537643135313932623237
66313863396463343232383131633531363239396636363165646562396261626633326561313837
32383634326230656230386237333561373630343233353239613463626538356338326633386434
36396639313030336165366266646431306665336662663732313762663938666239663233393964
30393733393331383132306463656636396566373961383865643562383564356363'''

TEST_VAULT_PASSWORD = '1234'

TEST_SSH_KEY_DATA = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAyQ8F5bbgjHvk4SZJsKI9OmJKMFxZqRhvx4LaqjLTKbBwRBsY
1/C00NPiZn70dKbeyV7RNVZxuzM6yd3D3lwTdbDu/eJ0x72t3ch+TdLt/aenyy10
IvZyhSlxCLDkDaVVPFYJOQzVS8TkdOi6ZHc+R0c0A+4ZE8OQ8C0zIKtUTHqRk4/v
gYK5guhNS0DdgWkBj6K+r/9D4bqdPTJPt4S7H75vb1tBgseiqftEkLYOhTK2gsCi
5uJgpG4zPQY4Kk/97dbW7pwcvPkr1rKkAwEJ27Bfo+DBv3oEx3SinpXQtOrH1aEO
RHSXldBaymdBtVLUhjxDlnnQ7Ps+fNX04R7N4QIDAQABAoIBAQClEDxbNyRqsVxa
q8BbzxZNVFxsD6Vceb9rIDa8/DT4SO4iO8zNm8QWnZ2FYDz5d/X3hGxlSa7dbVWa
XQJtD1K6kKPks4IEaejP58Ypxj20vWu4Fnz+Jy4lvLwb0n2n5lBv1IKF389NATw9
7sL3sB3lDsPZZiQYYbogNDuBWqc+kP0zD84bONsM/B2HMRm9BRv2UsZf+zKU4pTA
UqHffyjmw7LqHmbtVjwVcUsC+xcE4kCuWLvabFnTWOSnWECyIw2+trxKdwCXbfzG
s5rn4Dj+aEKimzFaRpTSVx6w4yw9xw/EjsSaZ88jKSpTP8ocCut6zv+P/JwlukEX
4A4FxqyxAoGBAOp3G9EIAAWijcIgO5OdiZNEqVyqd3yyPzT6d/q7bf4dpVCZiLNA
bRmge83aMc4g2Dpkn/++It3bDmnXXGg+BZSX5KT9JLklXchaw9phv9J0diZEUvYS
mSQafbUGIqYnYzns3TU0cbgITs1iVIEstHYjGr3J88nDG+HFCHboxa93AoGBANuG
cDFgyvm79+haK2fHhUCZgaFFYBpkpuz+zjDjzIytOzymWa2gD9jIa7mvdvoH2ge3
AVG0vy+n9cJaqJMuLkhdI01wVlqY9wvDHFyZCXyIvKVPMljKeTvCNGCupsG4R171
gSKT5ryOx58MGbE7knAZC+QWpwxFpdpbfej6g7NnAoGBAMz6ipAJbXN/tG0FnvAj
pxXfzizcPw/+CTI40tGaMMQbiN5ZC+CiL39bBUFnQ2mQ31jVheegg3zvuL8hb4EW
z+wjitoPEZ7nowC5EUaHdJr6BBzaWKkWg1nD6yhqj7ow7xfCE3YjPlQEt1fpYjV4
LuClOgi4WPCIKYUMq6TBRaprAoGAVrEjs0xPPApQH5EkXQp9BALbH23/Qs0G4sbJ
dKMxT0jGAPCMr7VrLKgRarXxXVImdy99NOAVNGO2+PbGZcEyA9/MJjO71nFb9mgp
1iOVjHmPThUVg90JvWC3QIsYTZ5RiR2Yzqfr0gDsslGb/9LPxLcPbBbKB12l3rKM
6amswvcCgYEAvgcSlTfAkI3ac8rB70HuDmSdqKblIiQjtPtT/ixXaFkZOmHRr4AE
KepMRDnaO/ldPDPEWCGqPzEM0t/0jS8/hCu3zLHHpZ+0LnHq+EXkOI0/GB4P+z5l
Vz3kouC0BTav0rCEnDop/cWMTiAp/XhKXfrTTTOra/F8l2xD8n/mnzY=
-----END RSA PRIVATE KEY-----'''

TEST_SSH_KEY_DATA_LOCKED = '''-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,6B4E92AF4C29DE26FD8535D81825BDE6

pg8YplxPpfzgEGUiko34DGaYklyGyYKXjOrGFGyLoquNAVNFyewT34dDrZi0IAaE
79wMVcdlHbrJfZz8ML8I/ft6zM6BdlwZExH4y9DRAaktY3yIXxSvowBQ6ljh3wUy
M6m0afOfVjT22V8hLFgX0yTQ6P9zTG1cmj6+JQWTsMJ5EP3rnFK5CyrJXP48B3GI
GgE66rkXDvcKlVeIrbrpcTyfmEpafPgVRJYCDFXxeO/BfKgUFVxFq1PgFbvGQMmD
wA6EsyRrN+aoub1sqzj8tM8e4nwEi0EifdRShkFeqH4GUOKypanTXfCqwFBgYi5a
i3YwSnniZZPwCniGR5cl8oetrc5dubq/IR0txsGi2lO6zJEWdSer/EadS0QAll4S
yXrSc/lFaez1VmVe/8aoBKDOHhe7jV3YXAuqCeB4o/SThB/9Gad44MTbqFH3d7cD
k+F0Cjup7LZqZpXeB7ZHRG/Yt9MtBzwDVmEWaxA1WIN5a8xyZEVzRswSi4lZX69z
Va7eTKcrCbHOQmIbLZGRiZbAbfgriwwxQCJWELv80h+A754Bhi23n3WzcT094fRi
cqK//HcHHXxYGmrfUbHYcj+GCQ07Uk2ZR3qglmPISUCgfZwM9k0LpXudWE8vmF2S
pAnbgxgrfUMtpu5EAO+d8Sn5wQLVD7YzPBUhM4PYfYUbJnRoZQryuR4lqCzcg0te
BM8x1LzSXyBEbQaonuMzSz1hCQ9hZpUwUEqDWAT3cPNmgyWkXQ1P8ehJhTmryGJw
/GHxNzMZDGj+bBKo7ic3r1g3ZmmlSU1EVxMLvRBKhdc1XicBVqepDma6/LEpj+5X
oplR+3Q0QSQ8CchcSxYtOpI3UBCatpyu09GtfzS+7bI5I7FVYUccR83+oQlKpPHC
5O2irB8JeXqAY679fx2N4i0E6l5Xr5AjUtOBCNil0Y70eOf9ER6i7kGakR7bUtk5
fQn8Em9pLsYYalnekn4sxyHpGq59KgNPjQiJRByYidSJ/oyNbmtPlxfXLwpuicd2
8HLm1e0UeGidfF/bSlySwDzy1ZlSr/Apdcn9ou5hfhaGuQvjr9SvJwxQFNRMPdHj
ukBSDGuxyyU+qBrWJhFsymiZAWDofY/4GzgMu4hh0PwN5arzoTxnLHmc/VFttyMx
nP7bTaa9Sr54TlMr7NuKTzz5biXKjqJ9AZKIUF2+ERebjV0hMpJ5NPsLwPUnA9kx
R3tl1JL2Ia82ovS81Ghff/cBZsx/+LQYa+ac4eDTyXxyg4ei5tPwOlzz7pDKJAr9
XEh2X6rywCNghEMZPaOQLiEDLJ2is6P4OarSa/yoU4OMetpFfwZ0oJSCmGlEa+CF
zeJ80yXhU1Ru2eqiUjCAUg25BFPwoiMJDc6jWWow7OrXCQsw7Ddo2ncy1p9QeWjM
2R4ojPHWuXKYxvwVSc8NZHASlycBCaxHLDAEyH4avOSDPWOB1H5t+RrNmo0qgush
0aRo6F7BjzB2rA4E+xu2u11TBfF8iB3PC919/vxnkXF97NqezsaCz6VbRlsU0A+B
wwoi+P4JlJF6ZuhuDv6mhmBCSdXdc1bvimvdpOljhThr+cG5mM08iqWGKdA665cw
-----END RSA PRIVATE KEY-----
'''

TEST_SSH_KEY_DATA_UNLOCK = 'unlockme'

@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class BaseCeleryTest(BaseLiveServerTest):
    '''
    Base class for celery task tests.
    '''

@override_settings(ANSIBLE_TRANSPORT='local')
class RunJobTest(BaseCeleryTest):
    '''
    Test cases for RunJob celery task.
    '''

    def setUp(self):
        super(RunJobTest, self).setUp()
        self.test_project_path = None
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.inventory = self.organization.inventories.create(name='test-inventory',
                                                              description='description for test-inventory')
        self.host = self.inventory.hosts.create(name='host.example.com')
        self.group = self.inventory.groups.create(name='test-group')
        self.group2 = self.inventory.groups.create(name='test-group2')
        self.group.hosts.add(self.host)
        self.group2.hosts.add(self.host)
        self.project = None
        self.credential = None
        self.cloud_credential = None
        settings.INTERNAL_API_URL = self.live_server_url
        if settings.CALLBACK_CONSUMER_PORT:
            self.start_queue(settings.CALLBACK_CONSUMER_PORT, settings.CALLBACK_QUEUE_PORT)

    def tearDown(self):
        super(RunJobTest, self).tearDown()
        if self.test_project_path:
            shutil.rmtree(self.test_project_path, True)
        self.terminate_queue()

    def create_test_credential(self, **kwargs):
        opts = {
            'name': 'test-creds',
            'kind': 'ssh',
            'user': self.super_django_user,
            'username': '',
            'ssh_key_data': '',
            'ssh_key_unlock': '',
            'password': '',
            'sudo_username': '',
            'sudo_password': '',
            'vault_password': '',
        }
        opts.update(kwargs)
        self.credential = Credential.objects.create(**opts)
        return self.credential

    def create_test_cloud_credential(self, **kwargs):
        opts = {
            'name': 'test-cloud-cred',
            'kind': 'aws',
            'user': self.super_django_user,
            'username': '',
            'password': '',
        }
        opts.update(kwargs)
        self.cloud_credential = Credential.objects.create(**opts)
        return self.cloud_credential

    def create_test_project(self, playbook_content, role_playbooks=None):
        self.project = self.make_projects(self.normal_django_user, 1,
                                          playbook_content, role_playbooks)[0]
        self.organization.projects.add(self.project)

    def create_test_job_template(self, **kwargs):
        opts = {
            'name': 'test-job-template %s' % str(now()),
            'inventory': self.inventory,
            'project': self.project,
            'credential': self.credential,
            'cloud_credential': self.cloud_credential,
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
        with impersonate(self.super_django_user):
            job_template = kwargs.pop('job_template', None)
            if job_template:
                self.job = job_template.create_job(**kwargs)
            else:
                opts = {
                    'inventory': self.inventory,
                    'project': self.project,
                    'credential': self.credential,
                    'cloud_credential': self.cloud_credential,
                    'job_type': 'run',
                }
                try:
                    opts['playbook'] = self.project.playbooks[0]
                except (AttributeError, IndexError):
                    pass
                opts.update(kwargs)
                self.job = Job.objects.create(**opts)
        return self.job

    def check_job_result(self, job, expected='successful', expect_stdout=True,
                         expect_traceback=False):
        msg = u'job status is %s, expected %s' % (job.status, expected)
        msg = u'%s\nargs:\n%s' % (msg, job.job_args)
        msg = u'%s\nenv:\n%s' % (msg, job.job_env)
        if job.result_traceback:
            msg = u'%s\ngot traceback:\n%s' % (msg, job.result_traceback)
        if job.result_stdout:
            msg = u'%s\ngot stdout:\n%s' % (msg, job.result_stdout)
        if isinstance(expected, (list, tuple)):
            self.assertTrue(job.status in expected)
        else:
            self.assertEqual(job.status, expected, msg)
        if expect_stdout:
            self.assertTrue(job.result_stdout)
        else:
            self.assertFalse(job.result_stdout,
                             u'expected no stdout, got:\n%s' %
                             job.result_stdout)
        if expect_traceback:
            self.assertTrue(job.result_traceback)
        else:
            self.assertFalse(job.result_traceback,
                             u'expected no traceback, got:\n%s' %
                             job.result_traceback)

    def check_job_events(self, job, runner_status='ok', plays=1, tasks=1,
                         async=False, async_timeout=False, async_nowait=False,
                         check_ignore_errors=False, async_tasks=0,
                         has_roles=False):
        job_events = job.job_events.all()
        if False and async:
            print
            qs = self.super_django_user.get_queryset(JobEvent)
            for je in qs.filter(job=job):
                print je.get_event_display2()
                print je.event, je, je.failed
                print je.event_data
                print
        for job_event in job_events:
            unicode(job_event)  # For test coverage.
            job_event.save()
            job_event.get_event_display2()
        should_be_failed = bool(runner_status not in ('ok', 'skipped'))
        should_be_changed = bool(runner_status in ('ok', 'failed') and
                                 job.job_type == 'run')
        host_pks = set([self.host.pk])
        qs = job_events.filter(event='playbook_on_start')
        self.assertEqual(qs.count(), 1)
        for evt in qs:
            self.assertFalse(evt.host, evt)
            self.assertFalse(evt.play, evt)
            self.assertFalse(evt.task, evt)
            self.assertFalse(evt.role, evt)
            self.assertEqual(evt.failed, should_be_failed)
            if not async:
                self.assertEqual(evt.changed, should_be_changed)
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self.assertEqual(set(evt.hosts.values_list('pk', flat=True)),
                                 host_pks)
        qs = job_events.filter(event='playbook_on_play_start')
        self.assertEqual(qs.count(), plays)
        for evt in qs:
            self.assertFalse(evt.host, evt)
            self.assertTrue(evt.play, evt)
            self.assertFalse(evt.task, evt)
            self.assertFalse(evt.role, evt)
            self.assertEqual(evt.failed, should_be_failed)
            self.assertEqual(evt.play, evt.event_data['name'])
            # All test playbooks have a play name set explicitly.
            self.assertNotEqual(evt.event_data['name'], evt.event_data['pattern'])
            if not async:
                self.assertEqual(evt.changed, should_be_changed)
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self.assertEqual(set(evt.hosts.values_list('pk', flat=True)),
                                 host_pks)
        qs = job_events.filter(event='playbook_on_task_start')
        self.assertEqual(qs.count(), tasks)
        for n, evt in enumerate(qs):
            self.assertFalse(evt.host, evt)
            self.assertTrue(evt.play, evt)
            self.assertTrue(evt.task, evt)
            if has_roles:
                self.assertTrue(evt.role, evt)
            else:
                self.assertFalse(evt.role, evt)
            if async and async_tasks < tasks and n == 0:
                self.assertFalse(evt.failed)
            else:
                self.assertEqual(evt.failed, should_be_failed)
            if not async:
                self.assertEqual(evt.changed, should_be_changed)
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self.assertEqual(set(evt.hosts.values_list('pk', flat=True)),
                                 host_pks)
        if check_ignore_errors:
            qs = job_events.filter(event='runner_on_failed')
        else:
            qs = job_events.filter(event=('runner_on_%s' % runner_status))
        if async and async_timeout:
            pass
        elif async:
            self.assertTrue(qs.count())
        else:
            self.assertEqual(qs.count(), tasks)
        for evt in qs:
            self.assertEqual(evt.host, self.host)
            self.assertTrue(evt.play, evt)
            self.assertTrue(evt.task, evt)
            self.assertTrue(evt.host_name)
            if has_roles:
                self.assertTrue(evt.role, evt)
            else:
                self.assertFalse(evt.role, evt)
            self.assertEqual(evt.failed, should_be_failed)
            if not async:
                self.assertEqual(evt.changed, should_be_changed)
            if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                self.assertEqual(set(evt.hosts.values_list('pk', flat=True)),
                                 host_pks)
        if async:
            qs = job_events.filter(event='runner_on_async_poll')
            if not async_nowait:
                self.assertTrue(qs.count())
            for evt in qs:
                self.assertEqual(evt.host, self.host)
                self.assertTrue(evt.play, evt)
                self.assertTrue(evt.task, evt)
                self.assertEqual(evt.failed, False)#should_be_failed)
                if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                    self.assertEqual(set(evt.hosts.values_list('pk', flat=True)),
                                     host_pks)
            qs = job_events.filter(event=('runner_on_async_%s' % runner_status))
            # Ansible 1.2 won't call the on_runner_async_failed callback when a
            # timeout occurs, so skip this check for now.
            if not async_timeout and not async_nowait:
                self.assertEqual(qs.count(), async_tasks)
            for evt in qs:
                self.assertEqual(evt.host, self.host)
                self.assertTrue(evt.play, evt)
                self.assertTrue(evt.task, evt)
                self.assertEqual(evt.failed, should_be_failed)
                if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
                    self.assertEqual(set(evt.hosts.values_list('pk', flat=True)),
                                     host_pks)
        qs = job_events.filter(event__startswith='runner_')
        if check_ignore_errors:
            qs = qs.exclude(event='runner_on_failed')
        else:
            qs = qs.exclude(event=('runner_on_%s' % runner_status))
        if async:
            if runner_status == 'failed':
                qs = qs.exclude(event='runner_on_ok')
            qs = qs.exclude(event='runner_on_async_poll')
            qs = qs.exclude(event=('runner_on_async_%s' % runner_status))
        self.assertEqual(qs.count(), 0)

    def test_run_job(self):
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'ok', 1, 2)
        for job_host_summary in job.job_host_summaries.all():
            unicode(job_host_summary)  # For test coverage.
            self.assertFalse(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary, job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertFalse(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertFalse(group.has_active_failures)
        self.assertFalse(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 1)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 1)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)
        return job

    def test_check_job(self):
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template, job_type='check')
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'skipped', 1, 2)
        for job_host_summary in job.job_host_summaries.all():
            self.assertFalse(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary, job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertFalse(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertFalse(group.has_active_failures)
        self.assertFalse(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 0)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 1)
        self.assertEqual(job.processed_hosts.count(), 1)
        return job

    def test_run_job_that_fails(self):
        self.create_test_project(TEST_PLAYBOOK2)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'failed')
        self.check_job_events(job, 'failed', 1, 1)
        for job_host_summary in job.job_host_summaries.all():
            self.assertTrue(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary, job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertTrue(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertTrue(group.has_active_failures)
        self.assertTrue(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 0)
        self.assertEqual(job.failed_hosts.count(), 1)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)
        return job

    def test_run_job_with_ignore_errors(self):
        self.create_test_project(TEST_IGNORE_ERRORS_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'ok', 1, 1, check_ignore_errors=True)
        for job_host_summary in job.job_host_summaries.all():
            self.assertFalse(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary, job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertFalse(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertFalse(group.has_active_failures)
        self.assertFalse(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 1)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 1)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_update_has_active_failures_when_inventory_changes(self):
        job = self.test_run_job_that_fails()
        # Add host to new group (should set has_active_failures)
        new_group = self.inventory.groups.create(name='new group')
        self.assertFalse(new_group.has_active_failures)
        new_group.hosts.add(self.host)
        new_group = Group.objects.get(pk=new_group.pk)
        self.assertTrue(new_group.has_active_failures)
        # Remove host from new group (should clear has_active_failures)
        new_group.hosts.remove(self.host)
        new_group = Group.objects.get(pk=new_group.pk)
        self.assertFalse(new_group.has_active_failures)
        # Add existing group to new group (should set flag)
        new_group.children.add(self.group)
        new_group = Group.objects.get(pk=new_group.pk)
        self.assertTrue(new_group.has_active_failures)
        # Remove existing group from new group (should clear flag)
        new_group.children.remove(self.group)
        new_group = Group.objects.get(pk=new_group.pk)
        self.assertFalse(new_group.has_active_failures)
        # Mark host inactive (should clear flag on parent group and inventory)
        self.host.mark_inactive()
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertFalse(self.group.has_active_failures)
        self.inventory = Inventory.objects.get(pk=self.inventory.pk)
        self.assertFalse(self.inventory.has_active_failures)
        # Un-mark host as inactive (need to force update of flag on group and
        # inventory)
        host = self.host
        host.name = '_'.join(host.name.split('_')[3:]) or 'undeleted host'
        host.active = True
        host.save()
        host.update_computed_fields()
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertTrue(self.group.has_active_failures)
        self.inventory = Inventory.objects.get(pk=self.inventory.pk)
        self.assertTrue(self.inventory.has_active_failures)
        # Delete host. (should clear flag)
        self.host.delete()
        self.host = None
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertFalse(self.group.has_active_failures)
        self.inventory = Inventory.objects.get(pk=self.inventory.pk)
        self.assertFalse(self.inventory.has_active_failures)

    def test_update_has_active_failures_when_job_removed(self):
        job = self.test_run_job_that_fails()
        # Mark job as inactive (should clear flags).
        job.mark_inactive()
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertFalse(self.host.has_active_failures)
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertFalse(self.group.has_active_failures)
        self.inventory = Inventory.objects.get(pk=self.inventory.pk)
        self.assertFalse(self.inventory.has_active_failures)
        # Un-mark job as inactive (need to force update of flag)
        job.active = True
        job.save()
        # Need to manually update last_job on host...
        host = Host.objects.get(pk=self.host.pk)
        host.last_job = job
        host.last_job_host_summary = JobHostSummary.objects.get(job=job, host=host)
        host.save()
        self.inventory.update_computed_fields()
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertTrue(self.host.has_active_failures)
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertTrue(self.group.has_active_failures)
        self.inventory = Inventory.objects.get(pk=self.inventory.pk)
        self.assertTrue(self.inventory.has_active_failures)
        # Delete job entirely.
        job.delete()
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertFalse(self.host.has_active_failures)
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertFalse(self.group.has_active_failures)
        self.inventory = Inventory.objects.get(pk=self.inventory.pk)
        self.assertFalse(self.inventory.has_active_failures)

    def test_update_host_last_job_when_job_removed(self):
        job1 = self.test_run_job()
        job2 = self.test_run_job()
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job2)
        self.assertEqual(self.host.last_job_host_summary.job, job2)
        # Delete job2 (should update host to point to job1).
        job2.delete()
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job1)
        self.assertEqual(self.host.last_job_host_summary.job, job1)
        # Mark job1 inactive (should update host.last_job to None).
        job1.mark_inactive()
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, None)
        self.assertEqual(self.host.last_job_host_summary, None)

    def test_check_job_where_task_would_fail(self):
        self.create_test_project(TEST_PLAYBOOK2)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template, job_type='check')
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        # Since we don't actually run the task, the --check should indicate
        # everything is successful.
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'skipped', 1, 1)
        for job_host_summary in job.job_host_summaries.all():
            self.assertFalse(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary, job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertFalse(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertFalse(group.has_active_failures)
        self.assertFalse(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 0)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 1)
        self.assertEqual(job.processed_hosts.count(), 1)

    def _cancel_job_callback(self):
        job = Job.objects.get(pk=self.job.pk)
        self.assertTrue(job.cancel())
        self.assertTrue(job.cancel())  # No change from calling again.

    def test_cancel_job(self):
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        # Pass save=False just for the sake of test coverage.
        job = self.create_test_job(job_template=job_template, save=False)
        job.save()
        self.assertEqual(job.status, 'new')
        self.assertEqual(job.cancel_flag, False)
        # Calling cancel before start has no effect.
        self.assertFalse(job.cancel())
        self.assertEqual(job.cancel_flag, False)
        self.assertFalse(job.passwords_needed_to_start)
        job.cancel_flag = True
        job.save()
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'canceled', expect_stdout=False)
        self.assertEqual(job.cancel_flag, True)
        # Calling cancel afterwards just returns the cancel flag.
        self.assertTrue(job.cancel())
        # Read attribute for test coverage.
        job.celery_task
        job.celery_task_id = ''
        job.save()
        self.assertEqual(job.celery_task, None)
        # Unable to start job again.
        self.assertFalse(job.signal_start())

    def test_extra_job_options(self):
        self.create_test_project(TEST_EXTRA_VARS_PLAYBOOK)
        # Test with extra_vars containing misc whitespace.
        job_template = self.create_test_job_template(forks=3, verbosity=2,
                                                     extra_vars=u'{\n\t"abc": 1234\n}')
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('--forks=3' in job.job_args)
        self.assertTrue('-vv' in job.job_args)
        self.assertTrue('-e' in job.job_args)
        # Test with extra_vars as key=value (old format).
        job_template2 = self.create_test_job_template(extra_vars='foo=1')
        job2 = self.create_test_job(job_template=job_template2)
        self.assertEqual(job2.status, 'new')
        self.assertTrue(job2.signal_start())
        job2 = Job.objects.get(pk=job2.pk)
        self.check_job_result(job2, 'successful')
        # Test with extra_vars as YAML (should be converted to JSON in args).
        job_template3 = self.create_test_job_template(extra_vars='abc: 1234')
        job3 = self.create_test_job(job_template=job_template3)
        self.assertEqual(job3.status, 'new')
        self.assertTrue(job3.signal_start())
        job3 = Job.objects.get(pk=job3.pk)
        self.check_job_result(job3, 'successful')

    def test_lots_of_extra_vars(self):
        self.create_test_project(TEST_EXTRA_VARS_PLAYBOOK)
        extra_vars = dict(('var_%d' % x, x) for x in xrange(200))
        job_template = self.create_test_job_template(extra_vars=extra_vars)
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.assertTrue(len(job.job_args) > 1024)
        self.check_job_result(job, 'successful')
        self.assertTrue('-e' in job.job_args)

    def test_limit_option(self):
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template(limit='bad.example.com')
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'failed')
        self.assertTrue('-l' in job.job_args)

    def test_limit_option_with_group_pattern_and_ssh_key(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA)
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template(limit='test-group:&test-group2')
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('--private-key=' in job.job_args)
        self.assertFalse('ssh-agent' in job.job_args)

    def test_ssh_username_and_password(self):
        self.create_test_credential(username='sshuser', password='sshpass')
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('-u' in job.job_args)
        self.assertTrue('--ask-pass' in job.job_args)

    def test_ssh_ask_password(self):
        self.create_test_credential(password='ASK')
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.passwords_needed_to_start)
        self.assertTrue('ssh_password' in job.passwords_needed_to_start)
        self.assertFalse(job.signal_start())
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.signal_start(ssh_password='sshpass'))
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('--ask-pass' in job.job_args)

    def test_sudo_username_and_password(self):
        self.create_test_credential(sudo_username='sudouser',
                                    sudo_password='sudopass')
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        # Job may fail if current user doesn't have password-less sudo
        # privileges, but we're mainly checking the command line arguments.
        self.check_job_result(job, ('successful', 'failed'))
        self.assertTrue('-U' in job.job_args)
        self.assertTrue('--ask-sudo-pass' in job.job_args)

    def test_sudo_ask_password(self):
        self.create_test_credential(sudo_password='ASK')
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.passwords_needed_to_start)
        self.assertTrue('sudo_password' in job.passwords_needed_to_start)
        self.assertFalse(job.signal_start())
        self.assertTrue(job.signal_start(sudo_password='sudopass'))
        job = Job.objects.get(pk=job.pk)
        # Job may fail if current user doesn't have password-less sudo
        # privileges, but we're mainly checking the command line arguments.
        self.assertTrue(job.status in ('successful', 'failed'))
        self.assertTrue('--ask-sudo-pass' in job.job_args)

    def test_unlocked_ssh_key(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA)
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('--private-key=' in job.job_args)
        self.assertFalse('ssh-agent' in job.job_args)

    def test_locked_ssh_key_with_password(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
                                    ssh_key_unlock=TEST_SSH_KEY_DATA_UNLOCK)
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('ssh-agent' in job.job_args)
        self.assertTrue('Bad passphrase' not in job.result_stdout)

    def test_locked_ssh_key_with_bad_password(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
                                    ssh_key_unlock='not the passphrase')
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'failed')
        self.assertTrue('ssh-agent' in job.job_args)
        self.assertTrue('Bad passphrase' in job.result_stdout)

    def test_locked_ssh_key_ask_password(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
                                    ssh_key_unlock='ASK')
        self.create_test_project(TEST_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.passwords_needed_to_start)
        self.assertTrue('ssh_key_unlock' in job.passwords_needed_to_start)
        self.assertFalse(job.signal_start())
        job.status = 'failed'
        job.save()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.signal_start(ssh_key_unlock=TEST_SSH_KEY_DATA_UNLOCK))
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue('ssh-agent' in job.job_args)
        self.assertTrue('Bad passphrase' not in job.result_stdout)

    def test_vault_password(self):
        self.create_test_credential(vault_password=TEST_VAULT_PASSWORD)
        self.create_test_project(TEST_VAULT_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        if Version(self.ansible_version) >= Version('1.5'):
            self.check_job_result(job, 'successful')
            self.assertTrue('--ask-vault-pass' in job.job_args)
        else:
            self.check_job_result(job, 'failed')
            self.assertFalse('--ask-vault-pass' in job.job_args)

    def test_vault_ask_password(self):
        self.create_test_credential(vault_password='ASK')
        self.create_test_project(TEST_VAULT_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.passwords_needed_to_start)
        self.assertTrue('vault_password' in job.passwords_needed_to_start)
        self.assertFalse(job.signal_start())
        self.assertEqual(job.status, 'new')
        self.assertTrue(job.signal_start(vault_password=TEST_VAULT_PASSWORD))
        job = Job.objects.get(pk=job.pk)
        if Version(self.ansible_version) >= Version('1.5'):
            self.check_job_result(job, 'successful')
            self.assertTrue('--ask-vault-pass' in job.job_args)
        else:
            self.check_job_result(job, 'failed')
            self.assertFalse('--ask-vault-pass' in job.job_args)

    def test_vault_bad_password(self):
        self.create_test_credential(vault_password='not it')
        self.create_test_project(TEST_VAULT_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'failed')
        if Version(self.ansible_version) >= Version('1.5'):
            self.assertTrue('--ask-vault-pass' in job.job_args)
        else:
            self.assertFalse('--ask-vault-pass' in job.job_args)

    def _test_cloud_credential_environment_variables(self, kind):
        if kind == 'aws':
            env_var1 = 'AWS_ACCESS_KEY'
            env_var2 = 'AWS_SECRET_KEY'
        elif kind == 'rax':
            env_var1 = 'RAX_USERNAME'
            env_var2 = 'RAX_API_KEY'
        self.create_test_cloud_credential(name='%s cred' % kind, kind=kind,
                                          username='my %s access' % kind,
                                          password='my %s secret' % kind)
        playbook = TEST_ENV_PLAYBOOK % {'env_var1': env_var1,
                                        'env_var2': env_var2}
        self.create_test_project(playbook)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.assertTrue(env_var1 in job.job_env)
        self.assertTrue(env_var2 in job.job_env)

    def test_aws_cloud_credential_environment_variables(self):
        self._test_cloud_credential_environment_variables('aws')

    def test_rax_cloud_credential_environment_variables(self):
        self._test_cloud_credential_environment_variables('rax')

    def test_run_async_job(self):
        self.create_test_project(TEST_ASYNC_OK_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'ok', 1, 2, async=True, async_tasks=1)
        for job_host_summary in job.job_host_summaries.all():
            self.assertFalse(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary,
                             job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertFalse(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertFalse(group.has_active_failures)
        self.assertFalse(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 1)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 1)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_run_async_job_that_fails(self):
        self.create_test_project(TEST_ASYNC_FAIL_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'failed')
        self.check_job_events(job, 'failed', 1, 2, async=True, async_tasks=1)
        for job_host_summary in job.job_host_summaries.all():
            self.assertTrue(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary,
                             job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertTrue(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertTrue(group.has_active_failures)
        self.assertTrue(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 1) # FIXME: Is this right?
        self.assertEqual(job.failed_hosts.count(), 1)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_run_async_job_that_times_out(self):
        self.create_test_project(TEST_ASYNC_TIMEOUT_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'failed')
        self.check_job_events(job, 'failed', 1, 2, async=True,
                              async_timeout=True, async_tasks=1)
        for job_host_summary in job.job_host_summaries.all():
            self.assertTrue(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary,
                             job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertTrue(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertTrue(group.has_active_failures)
        self.assertTrue(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 1) # FIXME: Is this right?
        self.assertEqual(job.failed_hosts.count(), 1)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_run_async_job_fire_and_forget(self):
        self.create_test_project(TEST_ASYNC_NOWAIT_PLAYBOOK)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'ok', 1, 1, async=True, async_nowait=True)
        for job_host_summary in job.job_host_summaries.all():
            self.assertFalse(job_host_summary.failed)
            self.assertEqual(job_host_summary.host.last_job_host_summary,
                             job_host_summary)
        self.host = Host.objects.get(pk=self.host.pk)
        self.assertEqual(self.host.last_job, job)
        self.assertFalse(self.host.has_active_failures)
        for group in self.host.all_groups:
            self.assertFalse(group.has_active_failures)
        self.assertFalse(self.host.inventory.has_active_failures)
        self.assertEqual(job.successful_hosts.count(), 1)
        self.assertEqual(job.failed_hosts.count(), 0)
        self.assertEqual(job.changed_hosts.count(), 0)
        self.assertEqual(job.unreachable_hosts.count(), 0)
        self.assertEqual(job.skipped_hosts.count(), 0)
        self.assertEqual(job.processed_hosts.count(), 1)

    def test_run_job_with_roles(self):
        self.create_test_project(TEST_PLAYBOOK_WITH_ROLES, TEST_ROLE_PLAYBOOKS)
        job_template = self.create_test_job_template()
        job = self.create_test_job(job_template=job_template)
        self.assertEqual(job.status, 'new')
        self.assertFalse(job.passwords_needed_to_start)
        self.assertTrue(job.signal_start())
        job = Job.objects.get(pk=job.pk)
        self.check_job_result(job, 'successful')
        self.check_job_events(job, 'ok', 1, 3, has_roles=True)
