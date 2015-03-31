# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
from distutils.version import StrictVersion as Version
import glob
import json
import os
import shutil
import subprocess
import tempfile
import unittest

# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.timezone import now

# Django-CRUM
from crum import impersonate

# AWX
from awx.main.models import * # noqa
from awx.main.tests.base import BaseJobExecutionTest
from awx.main.tests.tasks import TEST_SSH_KEY_DATA, TEST_SSH_KEY_DATA_LOCKED, TEST_SSH_CERT_KEY, TEST_SSH_KEY_DATA_UNLOCK

__all__ = ['RunAdHocCommandTest', 'AdHocCommandApiTest']


class BaseAdHocCommandTest(BaseJobExecutionTest):
    '''
    Common initialization for testing ad hoc commands.
    '''

    def setUp(self):
        super(BaseAdHocCommandTest, self).setUp()
        self.setup_instances()
        self.setup_users()
        self.organization = self.make_organizations(self.super_django_user, 1)[0]
        self.organization.admins.add(self.normal_django_user)
        self.inventory = self.organization.inventories.create(name='test-inventory', description='description for test-inventory')
        self.host = self.inventory.hosts.create(name='host.example.com')
        self.host2 = self.inventory.hosts.create(name='host2.example.com')
        self.group = self.inventory.groups.create(name='test-group')
        self.group2 = self.inventory.groups.create(name='test-group2')
        self.group.hosts.add(self.host)
        self.group2.hosts.add(self.host, self.host2)
        self.credential = None
        settings.INTERNAL_API_URL = self.live_server_url
        settings.CALLBACK_CONSUMER_PORT = ''

    def create_test_credential(self, **kwargs):
        self.credential = self.make_credential(**kwargs)
        return self.credential


class RunAdHocCommandTest(BaseAdHocCommandTest):
    '''
    Test cases for RunAdHocCommand celery task.
    '''

    def create_test_ad_hoc_command(self, **kwargs):
        with impersonate(self.super_django_user):
            opts = {
                'inventory': self.inventory,
                'credential': self.credential,
                'job_type': 'run',
                'module_name': 'command',
                'module_args': 'uptime',
            }
            opts.update(kwargs)
            self.ad_hoc_command = AdHocCommand.objects.create(**opts)
        return self.ad_hoc_command

    def check_ad_hoc_command_events(self, ad_hoc_command, runner_status='ok',
                                    hosts=None):
        ad_hoc_command_events = ad_hoc_command.ad_hoc_command_events.all()
        for ad_hoc_command_event in ad_hoc_command_events:
            unicode(ad_hoc_command_event)  # For test coverage.
        should_be_failed = bool(runner_status not in ('ok', 'skipped'))
        should_be_changed = bool(runner_status in ('ok', 'failed') and ad_hoc_command.job_type == 'run')
        if hosts is not None:
            host_pks = set([x.pk for x in hosts])
        else:
            host_pks = set(ad_hoc_command.inventory.hosts.values_list('pk', flat=True))
        qs = ad_hoc_command_events.filter(event=('runner_on_%s' % runner_status))
        self.assertEqual(qs.count(), len(host_pks))
        for evt in qs:
            self.assertTrue(evt.host_id in host_pks)
            self.assertTrue(evt.host_name)
            self.assertEqual(evt.failed, should_be_failed)
            self.assertEqual(evt.changed, should_be_changed)

    def test_run_ad_hoc_command(self):
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.check_ad_hoc_command_events(ad_hoc_command, 'ok')

    def test_check_mode_ad_hoc_command(self):
        ad_hoc_command = self.create_test_ad_hoc_command(module_name='ping', module_args='', job_type='check')
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.check_ad_hoc_command_events(ad_hoc_command, 'ok')

    def test_run_ad_hoc_command_that_fails(self):
        ad_hoc_command = self.create_test_ad_hoc_command(module_args='false')
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'failed')
        self.check_ad_hoc_command_events(ad_hoc_command, 'failed')

    def test_check_mode_where_command_would_fail(self):
        ad_hoc_command = self.create_test_ad_hoc_command(job_type='check', module_args='false')
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'failed')
        self.check_ad_hoc_command_events(ad_hoc_command, 'unreachable')

    def test_cancel_ad_hoc_command(self):
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.cancel_flag)
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        ad_hoc_command.cancel_flag = True
        ad_hoc_command.save(update_fields=['cancel_flag'])
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'canceled')
        self.assertTrue(ad_hoc_command.cancel_flag)
        # Calling cancel afterwards just returns the cancel flag.
        self.assertTrue(ad_hoc_command.cancel())
        # Read attribute for test coverage.
        ad_hoc_command.celery_task
        ad_hoc_command.celery_task_id = ''
        ad_hoc_command.save(update_fields=['celery_task_id'])
        self.assertEqual(ad_hoc_command.celery_task, None)
        # Unable to start ad hoc command again.
        self.assertFalse(ad_hoc_command.signal_start())

    def test_ad_hoc_command_options(self):
        ad_hoc_command = self.create_test_ad_hoc_command(forks=2, verbosity=2)
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.assertTrue('"--forks=2"' in ad_hoc_command.job_args)
        self.assertTrue('"-vv"' in ad_hoc_command.job_args)
        # Test with sudo privilege escalation.
        ad_hoc_command2 = self.create_test_ad_hoc_command(privilege_escalation='sudo')
        self.assertEqual(ad_hoc_command2.status, 'new')
        self.assertFalse(ad_hoc_command2.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command2.signal_start())
        ad_hoc_command2 = AdHocCommand.objects.get(pk=ad_hoc_command2.pk)
        self.check_job_result(ad_hoc_command2, ('successful', 'failed'))
        self.assertTrue('"--sudo"' in ad_hoc_command2.job_args)
        # Test with su privilege escalation.
        ad_hoc_command3 = self.create_test_ad_hoc_command(privilege_escalation='su')
        self.assertEqual(ad_hoc_command3.status, 'new')
        self.assertFalse(ad_hoc_command3.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command3.signal_start())
        ad_hoc_command3 = AdHocCommand.objects.get(pk=ad_hoc_command3.pk)
        self.check_job_result(ad_hoc_command3, ('successful', 'failed'))
        self.assertTrue('"--su"' in ad_hoc_command3.job_args)

    def test_limit_option(self):
        # Test limit by hostname.
        ad_hoc_command = self.create_test_ad_hoc_command(limit='host.example.com')
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.check_ad_hoc_command_events(ad_hoc_command, 'ok', hosts=[self.host])
        self.assertTrue('"host.example.com"' in ad_hoc_command.job_args)
        # Test limit by group name.
        ad_hoc_command2 = self.create_test_ad_hoc_command(limit='test-group')
        self.assertEqual(ad_hoc_command2.status, 'new')
        self.assertFalse(ad_hoc_command2.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command2.signal_start())
        ad_hoc_command2 = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command2, 'successful')
        self.check_ad_hoc_command_events(ad_hoc_command2, 'ok', hosts=[self.host])
        # Test limit by host not in inventory.
        ad_hoc_command3 = self.create_test_ad_hoc_command(limit='bad-host')
        self.assertEqual(ad_hoc_command3.status, 'new')
        self.assertFalse(ad_hoc_command3.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command3.signal_start())
        ad_hoc_command3 = AdHocCommand.objects.get(pk=ad_hoc_command3.pk)
        self.check_job_result(ad_hoc_command3, 'successful')
        self.check_ad_hoc_command_events(ad_hoc_command3, 'ok', hosts=[])
        self.assertEqual(ad_hoc_command3.ad_hoc_command_events.count(), 0)

    def test_ssh_username_and_password(self):
        self.create_test_credential(username='sshuser', password='sshpass')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.assertTrue('"-u"' in ad_hoc_command.job_args)
        self.assertTrue('"--ask-pass"' in ad_hoc_command.job_args)

    def test_ssh_ask_password(self):
        self.create_test_credential(password='ASK')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertTrue(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue('ssh_password' in ad_hoc_command.passwords_needed_to_start)
        self.assertFalse(ad_hoc_command.signal_start())
        self.assertTrue(ad_hoc_command.signal_start(ssh_password='sshpass'))
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.assertTrue('"--ask-pass"' in ad_hoc_command.job_args)

    def test_sudo_username_and_password(self):
        self.create_test_credential(sudo_username='sudouser',
                                    sudo_password='sudopass')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        # Job may fail if current user doesn't have password-less sudo
        # privileges, but we're mainly checking the command line arguments.
        self.check_job_result(ad_hoc_command, ('successful', 'failed'))
        self.assertTrue('"-U"' in ad_hoc_command.job_args)
        self.assertTrue('"--ask-sudo-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--sudo"' in ad_hoc_command.job_args)
        self.assertFalse('"-R"' in ad_hoc_command.job_args)
        self.assertFalse('"--ask-su-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--su"' in ad_hoc_command.job_args)

    def test_sudo_ask_password(self):
        self.create_test_credential(sudo_password='ASK')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertTrue(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue('sudo_password' in ad_hoc_command.passwords_needed_to_start)
        self.assertFalse(ad_hoc_command.signal_start())
        self.assertTrue(ad_hoc_command.signal_start(sudo_password='sudopass'))
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        # Job may fail, but we're mainly checking the command line arguments.
        self.check_job_result(ad_hoc_command, ('successful', 'failed'))
        self.assertTrue('"--ask-sudo-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--sudo"' in ad_hoc_command.job_args)
        self.assertFalse('"-R"' in ad_hoc_command.job_args)
        self.assertFalse('"--ask-su-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--su"' in ad_hoc_command.job_args)

    def test_su_username_and_password(self):
        self.create_test_credential(su_username='suuser', su_password='supass')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        # Job may fail, but we're mainly checking the command line arguments.
        self.check_job_result(ad_hoc_command, ('successful', 'failed'))
        self.assertTrue('"-R"' in ad_hoc_command.job_args)
        self.assertTrue('"--ask-su-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--su"' in ad_hoc_command.job_args)
        self.assertFalse('"-U"' in ad_hoc_command.job_args)
        self.assertFalse('"--ask-sudo-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--sudo"' in ad_hoc_command.job_args)

    def test_su_ask_password(self):
        self.create_test_credential(su_password='ASK')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertTrue(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue('su_password' in ad_hoc_command.passwords_needed_to_start)
        self.assertFalse(ad_hoc_command.signal_start())
        self.assertTrue(ad_hoc_command.signal_start(su_password='sudopass'))
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        # Job may fail, but we're mainly checking the command line arguments.
        self.check_job_result(ad_hoc_command, ('successful', 'failed'))
        self.assertTrue('"--ask-su-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--su"' in ad_hoc_command.job_args)
        self.assertFalse('"--ask-sudo-pass"' in ad_hoc_command.job_args)
        self.assertFalse('"--sudo"' in ad_hoc_command.job_args)

    def test_unlocked_ssh_key(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA)
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.assertFalse('"--private-key=' in ad_hoc_command.job_args)
        self.assertTrue('ssh-agent' in ad_hoc_command.job_args)

    def test_locked_ssh_key_with_password(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
                                    ssh_key_unlock=TEST_SSH_KEY_DATA_UNLOCK)
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.assertTrue('ssh-agent' in ad_hoc_command.job_args)
        self.assertTrue('Bad passphrase' not in ad_hoc_command.result_stdout)

    def test_locked_ssh_key_with_bad_password(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
                                    ssh_key_unlock='not the passphrase')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'failed')
        self.assertTrue('ssh-agent' in ad_hoc_command.job_args)
        self.assertTrue('Bad passphrase' in ad_hoc_command.result_stdout)

    def test_locked_ssh_key_ask_password(self):
        self.create_test_credential(ssh_key_data=TEST_SSH_KEY_DATA_LOCKED,
                                    ssh_key_unlock='ASK')
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertTrue(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue('ssh_key_unlock' in ad_hoc_command.passwords_needed_to_start)
        self.assertFalse(ad_hoc_command.signal_start())
        self.assertTrue(ad_hoc_command.signal_start(ssh_key_unlock='not it'))
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'failed')
        self.assertTrue('ssh-agent' in ad_hoc_command.job_args)
        self.assertTrue('Bad passphrase' in ad_hoc_command.result_stdout)
        # Try again and pass correct password.
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertTrue(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue('ssh_key_unlock' in ad_hoc_command.passwords_needed_to_start)
        self.assertFalse(ad_hoc_command.signal_start())
        self.assertTrue(ad_hoc_command.signal_start(ssh_key_unlock=TEST_SSH_KEY_DATA_UNLOCK))
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.assertTrue('ssh-agent' in ad_hoc_command.job_args)
        self.assertTrue('Bad passphrase' not in ad_hoc_command.result_stdout)

    def test_run_with_proot(self):
        # Only run test if proot is installed
        cmd = [getattr(settings, 'AWX_PROOT_CMD', 'proot'), '--version']
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.communicate()
            has_proot = bool(proc.returncode == 0)
        except (OSError, ValueError):
            has_proot = False
        if not has_proot:
            self.skipTest('proot is not installed')
        # Enable proot for this test.
        settings.AWX_PROOT_ENABLED = True
        # Hide local settings path.
        settings.AWX_PROOT_HIDE_PATHS = [os.path.join(settings.BASE_DIR, 'settings')]
        # Create list of paths that should not be visible to the command.
        hidden_paths = [
            os.path.join(settings.PROJECTS_ROOT, '*'),
            os.path.join(settings.JOBOUTPUT_ROOT, '*'),
        ]
        # Create a temp directory that should not be visible to the command.
        temp_path = tempfile.mkdtemp()
        self._temp_paths.append(temp_path)
        hidden_paths.append(temp_path)
        # Find a file in supervisor logs that should not be visible.
        try:
            supervisor_log_path = glob.glob('/var/log/supervisor/*')[0]
        except IndexError:
            supervisor_log_path = None
        if supervisor_log_path:
            hidden_paths.append(supervisor_log_path)
        # Create and run ad hoc command.
        module_args = ' && '.join(['echo %s && test ! -e %s' % (x, x) for x in hidden_paths])
        ad_hoc_command = self.create_test_ad_hoc_command(module_name='shell', module_args=module_args, verbosity=2)
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'successful')
        self.check_ad_hoc_command_events(ad_hoc_command, 'ok')

    def test_run_with_proot_not_installed(self):
        # Enable proot for this test, specify invalid proot cmd.
        settings.AWX_PROOT_ENABLED = True
        settings.AWX_PROOT_CMD = 'PR00T'
        ad_hoc_command = self.create_test_ad_hoc_command()
        self.assertEqual(ad_hoc_command.status, 'new')
        self.assertFalse(ad_hoc_command.passwords_needed_to_start)
        self.assertTrue(ad_hoc_command.signal_start())
        ad_hoc_command = AdHocCommand.objects.get(pk=ad_hoc_command.pk)
        self.check_job_result(ad_hoc_command, 'error', expect_traceback=True)


class AdHocCommandApiTest(BaseAdHocCommandTest):
    '''
    Test API list/detail views for ad hoc commands.
    '''

    def setUp(self):
        super(AdHocCommandApiTest, self).setUp()
        self.create_test_credential(user=self.normal_django_user)

    def test_ad_hoc_command_list(self):
        url = reverse('api:ad_hoc_command_list')

        # Retrieve the empty list of ad hoc commands.
        qs = AdHocCommand.objects.none()
        self.check_get_list(url, 'admin', qs)
        self.check_get_list(url, 'normal', qs)
        self.check_get_list(url, 'other', qs)
        self.check_get_list(url, 'nobody', qs)
        self.check_get_list(url, None, qs, expect=401)

        # Post to list to start a new ad hoc command.  Only admin and normal
        # user (org admin) can run commands by default.
        data = {
            'inventory': self.inventory.pk,
            'credential': self.credential.pk,
            'module_name': 'command',
            'module_args': 'uptime',
        }
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
            self.assertEqual(response['job_type'], 'run')
            self.assertEqual(response['inventory'], self.inventory.pk)
            self.assertEqual(response['credential'], self.credential.pk)
            self.assertEqual(response['module_name'], 'command')
            self.assertEqual(response['module_args'], 'uptime')
            self.assertEqual(response['limit'], '')
            self.assertEqual(response['forks'], 0)
            self.assertEqual(response['verbosity'], 0)
            self.assertEqual(response['privilege_escalation'], '')
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user('normal'):
            response = self.post(url, data, expect=201)
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user('other'):
            response = self.post(url, data, expect=403)
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user('nobody'):
            response = self.post(url, data, expect=403)
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user(None):
            response = self.post(url, data, expect=401)
            self.put(url, data, expect=401)
            self.patch(url, data, expect=401)
            self.delete(url, expect=401)

        # Retrieve the list of ad hoc commands (only admin/normal can see by default).
        qs = AdHocCommand.objects.all()
        self.assertEqual(qs.count(), 2)
        self.check_get_list(url, 'admin', qs)
        self.check_get_list(url, 'normal', qs)
        qs = AdHocCommand.objects.none()
        self.check_get_list(url, 'other', qs)
        self.check_get_list(url, 'nobody', qs)
        self.check_get_list(url, None, qs, expect=401)

        # Explicitly give other user admin permission on the inventory (still
        # not allowed to run ad hoc commands).
        user_perm_url = reverse('api:user_permissions_list', args=(self.other_django_user.pk,))
        user_perm_data = {
            'name': 'Allow Other to Admin Inventory',
            'inventory': self.inventory.pk,
            'permission_type': 'admin',
        }
        with self.current_user('admin'):
            response = self.post(user_perm_url, user_perm_data, expect=201)
            user_perm_id = response['id']
        with self.current_user('other'):
            response = self.post(url, data, expect=403)
        self.check_get_list(url, 'other', qs)

        # Update permission to allow other user to run ad hoc commands. Fails
        # when other user can't read credential.
        user_perm_url = reverse('api:permission_detail', args=(user_perm_id,))
        user_perm_data.update({
            'name': 'Allow Other to Admin Inventory and Run Ad Hoc Commands',
            'run_ad_hoc_commands': True,
        })
        with self.current_user('admin'):
            response = self.patch(user_perm_url, user_perm_data, expect=200)
        with self.current_user('other'):
            response = self.post(url, data, expect=403)

        # Succeeds once other user has a readable credential.  Other user can
        # only see his own ad hoc command (because of credential permissions).
        other_cred = self.create_test_credential(user=self.other_django_user)
        credential_id = data.pop('credential')
        data['credential'] = other_cred.pk
        with self.current_user('other'):
            response = self.post(url, data, expect=201)
        qs = AdHocCommand.objects.filter(created_by=self.other_django_user)
        self.assertEqual(qs.count(), 1)
        self.check_get_list(url, 'other', qs)

        # Explicitly give nobody user read permission on the inventory.
        user_perm_url = reverse('api:user_permissions_list', args=(self.nobody_django_user.pk,))
        user_perm_data = {
            'name': 'Allow Nobody to Read Inventory',
            'inventory': self.inventory.pk,
            'permission_type': 'read',
        }
        with self.current_user('admin'):
            response = self.post(user_perm_url, user_perm_data, expect=201)
            user_perm_id = response['id']
        with self.current_user('nobody'):
            response = self.post(url, data, expect=403)
        self.check_get_list(url, 'other', qs)

        # Create a cred for the nobody user, run an ad hoc command as the admin
        # user with that cred.  Nobody user can still not see the ad hoc command
        # without the run_ad_hoc_commands permission flag.
        nobody_cred = self.create_test_credential(user=self.nobody_django_user)
        credential_id = data.pop('credential')
        data['credential'] = nobody_cred.pk
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
        qs = AdHocCommand.objects.none()
        self.check_get_list(url, 'nobody', qs)

        # Give the nobody user the run_ad_hoc_commands flag, and can now see
        # the one ad hoc command previously run.
        user_perm_url = reverse('api:permission_detail', args=(user_perm_id,))
        user_perm_data.update({
            'name': 'Allow Nobody to Read Inventory and Run Ad Hoc Commands',
            'run_ad_hoc_commands': True,
        })
        with self.current_user('admin'):
            response = self.patch(user_perm_url, user_perm_data, expect=200)
        qs = AdHocCommand.objects.filter(credential_id=data['credential'])
        self.assertEqual(qs.count(), 1)
        self.check_get_list(url, 'nobody', qs)
        data['credential'] = credential_id

        # Post without inventory (should fail).
        inventory_id = data.pop('inventory')
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['inventory'] = inventory_id

        # Post without credential (should fail).
        credential_id = data.pop('credential')
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['credential'] = credential_id

        # Post with empty or unsupported module name (empty defaults to command).
        module_name = data.pop('module_name')
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
            self.assertEqual(response['module_name'], 'command')
        data['module_name'] = ''
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
            self.assertEqual(response['module_name'], 'command')
        data['module_name'] = 'transcombobulator'
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['module_name'] = module_name

        # Post with empty module args for shell/command modules (should fail),
        # empty args for other modules ok.
        module_args = data.pop('module_args')
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['module_name'] = 'shell'
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['module_args'] = ''
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['module_name'] = 'ping'
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
        data['module_name'] = module_name
        data['module_args'] = module_args

        # Post with invalid values for other parameters.
        data['job_type'] = 'something'
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['job_type'] = 'check'
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
            self.assertEqual(response['job_type'], 'check')
        data.pop('job_type')
        data['verbosity'] = -1
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data.pop('verbosity')
        data['forks'] = -1
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data.pop('forks')
        data['privilege_escalation'] = 'telekinesis'
        with self.current_user('admin'):
            response = self.post(url, data, expect=400)
        data['privilege_escalation'] = 'su'
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
            self.assertEqual(response['privilege_escalation'], 'su')
        data['privilege_escalation'] = 'sudo'
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)
            self.assertEqual(response['privilege_escalation'], 'sudo')

    def test_ad_hoc_command_detail(self):
        # Post to list to start a new ad hoc command.
        url = reverse('api:ad_hoc_command_list')
        data = {
            'inventory': self.inventory.pk,
            'credential': self.credential.pk,
            'module_name': 'command',
            'module_args': 'uptime',
        }
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)

        # Retrieve detail for ad hoc command.  Only GET is supported.
        url = reverse('api:ad_hoc_command_detail', args=(response['id'],))
        self.assertEqual(url, response['url'])
        with self.current_user('admin'):
            response = self.get(url, expect=200)
            self.assertEqual(response['related']['credential'],
                             reverse('api:credential_detail', args=(self.credential.pk,)))
            self.assertEqual(response['related']['inventory'],
                             reverse('api:inventory_detail', args=(self.inventory.pk,)))
            self.assertTrue(response['related']['stdout'])
            self.assertTrue(response['related']['cancel'])
            self.assertTrue(response['related']['relaunch'])
            self.assertTrue(response['related']['events'])
            self.assertTrue(response['related']['activity_stream'])
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user('normal'):
            response = self.get(url, expect=200)
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user('other'):
            response = self.get(url, expect=403)
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user('nobody'):
            response = self.get(url, expect=403)
            self.put(url, data, expect=405)
            self.patch(url, data, expect=405)
            self.delete(url, expect=405)
        with self.current_user(None):
            response = self.get(url, expect=401)
            self.put(url, data, expect=401)
            self.patch(url, data, expect=401)
            self.delete(url, expect=401)

    def test_ad_hoc_command_cancel(self):
        # Post to list to start a new ad hoc command.
        url = reverse('api:ad_hoc_command_list')
        data = {
            'inventory': self.inventory.pk,
            'credential': self.credential.pk,
            'module_name': 'command',
            'module_args': 'uptime',
        }
        with self.current_user('admin'):
            response = self.post(url, data, expect=201)

        url = reverse('api:ad_hoc_command_cancel', args=(response['id'],))
        self.assertEqual(url, response['related']['cancel'])

        # FIXME: Finish test.

    def test_ad_hoc_command_relaunch(self):
        self.skipTest('Not yet implemented')

    def test_ad_hoc_command_events_list(self):
        self.skipTest('Not yet implemented')

    def test_ad_hoc_command_event_detail(self):
        self.skipTest('Not yet implemented')

    def test_ad_hoc_command_activity_stream(self):
        self.skipTest('Not yet implemented')

    def test_inventory_ad_hoc_commands_list(self):
        self.skipTest('Not yet implemented')

    def test_host_ad_hoc_commands_list(self):
        self.skipTest('Not yet implemented')

    def test_group_ad_hoc_commands_list(self):
        self.skipTest('Not yet implemented')

    def test_host_ad_hoc_command_events_list(self):
        self.skipTest('Not yet implemented')
