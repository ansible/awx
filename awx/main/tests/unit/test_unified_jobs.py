# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import mock
from mock import Mock
from StringIO import StringIO
from django.utils.timezone import now

# AWX
from awx.main.models import UnifiedJob


# stdout file present
@mock.patch('os.path.exists', return_value=True)
@mock.patch('codecs.open', return_value='my_file_handler')
def test_result_stdout_raw_handle_file__found(exists, open):
    unified_job = UnifiedJob()
    unified_job.result_stdout_file = 'dummy'

    with mock.patch('os.stat', return_value=Mock(st_size=1)):
        result = unified_job.result_stdout_raw_handle()

    assert result == 'my_file_handler'


# stdout file missing, job finished
@mock.patch('os.path.exists', return_value=False)
def test_result_stdout_raw_handle__missing(exists):
    unified_job = UnifiedJob()
    unified_job.result_stdout_file = 'dummy'
    unified_job.finished = now()

    result = unified_job.result_stdout_raw_handle()

    assert isinstance(result, StringIO)
    assert result.read() == 'stdout capture is missing'


# stdout file missing, job not finished
@mock.patch('os.path.exists', return_value=False)
def test_result_stdout_raw_handle__pending(exists):
    unified_job = UnifiedJob()
    unified_job.result_stdout_file = 'dummy'
    unified_job.finished = None

    result = unified_job.result_stdout_raw_handle()

    assert isinstance(result, StringIO)
    assert result.read() == 'Waiting for results...'
