# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Python
import pytest
from unittest import mock
from datetime import timedelta

# Django
from django.utils import timezone

# AWX
from awx.main.models import (
    Job,
    JobEvent,
)
from awx.main.management.commands.replay_job_events import (
    ReplayJobEvents,
)


class TestReplayJobEvents():

    @pytest.fixture
    def epoch(self):
        return timezone.now()

    @pytest.fixture
    def job_events(self, epoch):
        return [
            JobEvent(created=epoch),
            JobEvent(created=epoch + timedelta(seconds=10)),
            JobEvent(created=epoch + timedelta(seconds=20)),
            JobEvent(created=epoch + timedelta(seconds=30)),
            JobEvent(created=epoch + timedelta(seconds=31)),
            JobEvent(created=epoch + timedelta(seconds=31, milliseconds=1)),
            JobEvent(created=epoch + timedelta(seconds=31, microseconds=1, milliseconds=1)),
        ]

    @pytest.fixture
    def mock_serializer_fn(self):
        class MockSerializer():
            data = dict()


        def fn(job_event):
            serialized = MockSerializer()
            serialized.data['group_name'] = 'foobar'
            return serialized
        return fn

    @pytest.fixture
    def replayer(self, mocker, job_events, mock_serializer_fn):
        r = ReplayJobEvents()
        r.get_serializer = lambda self: mock_serializer_fn
        r.get_job = mocker.MagicMock(return_value=Job(id=3))
        r.sleep = mocker.MagicMock()
        r.get_job_events = lambda self: (job_events, len(job_events))
        r.replay_offset = lambda *args, **kwarg: 0
        r.emit_job_status = lambda job, status: True
        return r

    @mock.patch('awx.main.management.commands.replay_job_events.emit_event_detail', lambda *a, **kw: None)
    def test_sleep(self, mocker, replayer):
        replayer.run(3, 1)

        assert replayer.sleep.call_count == 6
        replayer.sleep.assert_has_calls([
            mock.call(10.0),
            mock.call(10.0),
            mock.call(10.0),
            mock.call(1.0),
            mock.call(0.001),
            mock.call(0.000001),
        ])

    @mock.patch('awx.main.management.commands.replay_job_events.emit_event_detail', lambda *a, **kw: None)
    def test_speed(self, mocker, replayer):
        replayer.run(3, 2)

        assert replayer.sleep.call_count == 6
        replayer.sleep.assert_has_calls([
            mock.call(5.0),
            mock.call(5.0),
            mock.call(5.0),
            mock.call(0.5),
            mock.call(0.0005),
            mock.call(0.0000005),
        ])

    # TODO: Test replay_offset()
    # TODO: Test stat generation
