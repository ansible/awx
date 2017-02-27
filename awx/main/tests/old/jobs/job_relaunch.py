# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import
import json
import os
import unittest2 as unittest

# Django
from django.core.urlresolvers import reverse

# AWX
from awx.main.models import * # noqa
from awx.main.tests.base import BaseLiveServerTest
from awx.main.tests.job_base import BaseJobTestMixin

__all__ = ['JobRelaunchTest',]


@unittest.skipIf(os.environ.get('SKIP_SLOW_TESTS', False), 'Skipping slow test')
class JobRelaunchTest(BaseJobTestMixin, BaseLiveServerTest):

    def test_job_relaunch(self):
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'success')
        url = reverse('api:job_relaunch', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.post(url, {}, expect=201)
            j = Job.objects.get(pk=response['job'])
            self.assertTrue(j.status == 'successful')
            self.assertEqual(j.launch_type, 'relaunch')
        # Test with a job that prompts for SSH and sudo passwords.
        job = self.make_job(self.jt_sup_run, self.user_sue, 'success')
        url = reverse('api:job_start', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertEqual(set(response['passwords_needed_to_start']),
                             set(['ssh_password', 'become_password']))
            data = dict()
            response = self.post(url, data, expect=400)
            data['ssh_password'] = 'sshpass'
            response = self.post(url, data, expect=400)
            data2 = dict(become_password='sudopass')
            response = self.post(url, data2, expect=400)
            data.update(data2)
            response = self.post(url, data, expect=202)
            job = Job.objects.get(pk=job.pk)

    # Create jt with no extra_vars
    # Launch j1 with runtime extra_vars
    # Assign extra_vars to jt backing job
    # Relaunch j1
    # j2 should not contain jt extra_vars
    def test_relaunch_job_does_not_inherit_jt_extra_vars(self):
        jt_extra_vars = {
            "hello": "world"
        }
        j_extra_vars = {
            "goodbye": "cruel universe"
        }
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'success', extra_vars=j_extra_vars)
        url = reverse('api:job_relaunch', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.post(url, {}, expect=201)
            j = Job.objects.get(pk=response['job'])
            self.assertTrue(j.status == 'successful')

            self.jt_ops_east_run.extra_vars = jt_extra_vars
            self.jt_ops_east_run.save()

            response = self.post(url, {}, expect=201)
            j = Job.objects.get(pk=response['job'])
            self.assertTrue(j.status == 'successful')

            resp_extra_vars = json.loads(response['extra_vars'])
            self.assertNotIn("hello", resp_extra_vars)
            self.assertEqual(resp_extra_vars, j_extra_vars)


