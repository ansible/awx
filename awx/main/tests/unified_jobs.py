# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import mock
from StringIO import StringIO
from django.utils.timezone import now

# Django
from django.test import SimpleTestCase

# AWX
from awx.main.models import * # noqa

__all__ = ['UnifiedJobsUnitTest',]

class UnifiedJobsUnitTest(SimpleTestCase):

    # stdout file present
    @mock.patch('os.path.exists', return_value=True)
    @mock.patch('codecs.open', return_value='my_file_handler')
    def test_result_stdout_raw_handle_file__found(self, exists, open):
        unified_job = UnifiedJob()
        unified_job.result_stdout_file = 'dummy'

        result = unified_job.result_stdout_raw_handle()

        self.assertEqual(result, 'my_file_handler')

    # stdout file missing, job finished
    @mock.patch('os.path.exists', return_value=False)
    def test_result_stdout_raw_handle__missing(self, exists):
        unified_job = UnifiedJob()
        unified_job.result_stdout_file = 'dummy'
        unified_job.finished = now()

        result = unified_job.result_stdout_raw_handle()

        self.assertIsInstance(result, StringIO)
        self.assertEqual(result.read(), 'stdout capture is missing')

    # stdout file missing, job not finished
    @mock.patch('os.path.exists', return_value=False)
    def test_result_stdout_raw_handle__pending(self, exists):
        unified_job = UnifiedJob()
        unified_job.result_stdout_file = 'dummy'
        unified_job.finished = None

        result = unified_job.result_stdout_raw_handle()

        self.assertIsInstance(result, StringIO)
        self.assertEqual(result.read(), 'Waiting for results...')

