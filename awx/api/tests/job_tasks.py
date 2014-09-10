# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved.

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from django.test.utils import override_settings

from rest_framework.test import APIClient

import mock

from awx.api.views import JobJobTasksList
from awx.main.models import Job, JobTemplate, JobEvent
from awx.main.tests.jobs import BaseJobTestMixin


@override_settings(CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CALLBACK_CONSUMER_PORT='',
                   ANSIBLE_TRANSPORT='local')
class JobTasksTests(BaseJobTestMixin, LiveServerTestCase):
    """A set of tests to ensure that the job_tasks endpoint, available at
    `/api/v1/jobs/{id}/job_tasks/`, works as expected.
    """
    def setUp(self):
        super(JobTasksTests, self).setUp()
        settings.INTERNAL_API_URL = self.live_server_url

    def test_tasks_endpoint(self):
        """Establish that the `job_tasks` endpoint shows what we expect,
        which is a rollup of information about each of the corresponding
        job events.
        """
        # Create a job
        job = self.make_job(self.jt_ops_east_run, self.user_sue, 'new')
        job.signal_start()

        # Get the initial job event.
        event = job.job_events.get(event='playbook_on_play_start')

        # Actually make the request for the job tasks.
        with self.current_user(self.user_sue):
            url = '/api/v1/jobs/%d/job_tasks/?event_id=%d' % (job.id, event.id)
            response = self.get(url)

        # Test to make sure we got back what we expected.
        result = response['results'][0]
        self.assertEqual(result['host_count'], 7)
        self.assertEqual(result['changed_count'], 7)
        self.assertFalse(result['failed'])
        self.assertTrue(result['changed'])
