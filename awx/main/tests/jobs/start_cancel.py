# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from __future__ import absolute_import

# Django
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.utils import override_settings

# AWX
import django
from awx.main.models import * # noqa
from awx.main.tests.base import BaseLiveServerTest
from .base import BaseJobTestMixin

__all__ = ['JobStartCancelTest',]

class JobStartCancelTest(BaseJobTestMixin, BaseLiveServerTest):

    def test_job_start(self):
        #job = self.job_ops_east_run
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'success')
        url = reverse('api:job_start', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)
        self.check_invalid_auth(url, methods=('post',))

        # Sue can start a job (when passwords are already saved) as long as the
        # status is new.  Reverse list so "new" will be last.
        for status in reversed([x[0] for x in Job.STATUS_CHOICES]):
            if status == 'waiting':
                continue
            job.status = status
            job.save()
            with self.current_user(self.user_sue):
                response = self.get(url)
                if status == 'new':
                    self.assertTrue(response['can_start'])
                    self.assertFalse(response['passwords_needed_to_start'])
                    # response = self.post(url, {}, expect=202)
                    # job = Job.objects.get(pk=job.pk)
                    # self.assertEqual(job.status, 'successful',
                    #                  job.result_stdout)
                else:
                    self.assertFalse(response['can_start'])
                    response = self.post(url, {}, expect=405)

        # Test with a job that prompts for SSH and sudo become passwords.
        #job = self.job_sup_run
        job = self.make_job(self.jt_sup_run, self.user_sue, 'new')
        url = reverse('api:job_start', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertTrue(response['can_start'])
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
            # FIXME: Test run gets the following error in this case:
            #   fatal: [hostname] => sudo output closed while waiting for password prompt:
            #self.assertEqual(job.status, 'successful')

        # Test with a job that prompts for SSH unlock key, given the wrong key.
        #job = self.jt_ops_west_run.create_job(
        #    credential=self.cred_greg,
        #    created_by=self.user_sue,
        #)
        job = self.make_job(self.jt_ops_west_run, self.user_sue, 'new')
        job.credential = self.cred_greg
        job.save()

        url = reverse('api:job_start', args=(job.pk,))
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
            # job = Job.objects.get(pk=job.pk)
            # self.assertEqual(job.status, 'failed')

        # Test with a job that prompts for SSH unlock key, given the right key.
        from awx.main.tests.tasks import TEST_SSH_KEY_DATA_UNLOCK
        # job = self.jt_ops_west_run.create_job(
        #     credential=self.cred_greg,
        #     created_by=self.user_sue,
        # )
        job = self.make_job(self.jt_ops_west_run, self.user_sue, 'new')
        job.credential = self.cred_greg
        job.save()
        url = reverse('api:job_start', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertTrue(response['can_start'])
            self.assertEqual(set(response['passwords_needed_to_start']),
                             set(['ssh_key_unlock']))
            data = dict()
            response = self.post(url, data, expect=400)
            data['ssh_key_unlock'] = TEST_SSH_KEY_DATA_UNLOCK
            response = self.post(url, data, expect=202)
            # job = Job.objects.get(pk=job.pk)
            # self.assertEqual(job.status, 'successful')

        # FIXME: Test with other users, test when passwords are required.

    def test_job_relaunch(self):
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'success')
        url = reverse('api:job_relaunch', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.post(url, {}, expect=201)
            j = Job.objects.get(pk=response['job'])
            self.assertTrue(j.status == 'successful')
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

    def test_job_cancel(self):
        #job = self.job_ops_east_run
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'new')
        url = reverse('api:job_cancel', args=(job.pk,))

        # Test with no auth and with invalid login.
        self.check_invalid_auth(url)
        self.check_invalid_auth(url, methods=('post',))

        # sue can cancel the job, but only when it is pending or running.
        for status in [x[0] for x in Job.STATUS_CHOICES]:
            if status == 'waiting':
                continue
            job.status = status
            job.save()
            with self.current_user(self.user_sue):
                response = self.get(url)
                if status in ('new', 'pending', 'waiting', 'running'):
                    self.assertTrue(response['can_cancel'])
                    response = self.post(url, {}, expect=202)
                else:
                    self.assertFalse(response['can_cancel'])
                    response = self.post(url, {}, expect=405)

        # FIXME: Test with other users.

    def test_get_job_results(self):
        # Start/run a job and then access its results via the API.
        #job = self.job_ops_east_run
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'new')
        job.signal_start()

        # Check that the job detail has been updated.
        url = reverse('api:job_detail', args=(job.pk,))
        with self.current_user(self.user_sue):
            response = self.get(url)
            self.assertEqual(response['status'], 'successful',
                             response['result_traceback'])
            self.assertTrue(response['result_stdout'])

        # Test job events for completed job.
        url = reverse('api:job_job_events_list', args=(job.pk,))
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
            url = reverse('api:job_event_detail', args=(job_event.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)

        # Also test job event list for each host.
        if getattr(settings, 'CAPTURE_JOB_EVENT_HOSTS', False):
            for host in Host.objects.filter(pk__in=host_ids):
                url = reverse('api:host_job_events_list', args=(host.pk,))
                with self.current_user(self.user_sue):
                    response = self.get(url)
                    qs = host.job_events.all()
                    self.assertTrue(qs.count())
                    self.check_pagination_and_size(response, qs.count())
                    self.check_list_ids(response, qs)

        # Test job event list for groups.
        for group in self.inv_ops_east.groups.all():
            url = reverse('api:group_job_events_list', args=(group.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = group.job_events.all()
                self.assertTrue(qs.count(), group)
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)

        # Test global job event list.
        url = reverse('api:job_event_list')
        with self.current_user(self.user_sue):
            response = self.get(url)
            qs = JobEvent.objects.all()
            self.assertTrue(qs.count())
            self.check_pagination_and_size(response, qs.count())
            self.check_list_ids(response, qs)

        # Test job host summaries for completed job.
        url = reverse('api:job_job_host_summaries_list', args=(job.pk,))
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
            url = reverse('api:job_host_summary_detail',
                          args=(job_host_summary.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)

        # Test job host summaries for each host.
        for host in Host.objects.filter(pk__in=host_ids):
            url = reverse('api:host_job_host_summaries_list', args=(host.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = host.job_host_summaries.all()
                self.assertTrue(qs.count())
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)

        # Test job host summaries for groups.
        for group in self.inv_ops_east.groups.all():
            url = reverse('api:group_job_host_summaries_list', args=(group.pk,))
            with self.current_user(self.user_sue):
                response = self.get(url)
                qs = group.job_host_summaries.all()
                self.assertTrue(qs.count())
                self.check_pagination_and_size(response, qs.count())
                self.check_list_ids(response, qs)
