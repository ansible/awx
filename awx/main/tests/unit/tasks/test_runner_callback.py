import json
import os
import tempfile
from unittest import mock

from awx.main.tasks.callback import RunnerCallback, try_load_query_file
from awx.main.constants import ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE

from django.utils.translation import gettext_lazy as _


def test_delay_update(mock_me):
    rc = RunnerCallback()
    rc.delay_update(foo='bar')
    assert rc.extra_update_fields == {'foo': 'bar'}
    rc.delay_update(foo='foobar')
    assert rc.extra_update_fields == {'foo': 'foobar'}
    rc.delay_update(bar='foo')
    assert rc.get_delayed_update_fields() == {'foo': 'foobar', 'bar': 'foo', 'emitted_events': 0}


def test_delay_update_skip_if_set(mock_me):
    rc = RunnerCallback()
    rc.delay_update(foo='bar', skip_if_already_set=True)
    assert rc.extra_update_fields == {'foo': 'bar'}
    rc.delay_update(foo='foobar', skip_if_already_set=True)
    assert rc.extra_update_fields == {'foo': 'bar'}


def test_delay_update_failure_fields(mock_me):
    rc = RunnerCallback()
    rc.delay_update(job_explanation='1')
    rc.delay_update(job_explanation=_('2'))
    assert rc.extra_update_fields == {'job_explanation': '1\n2'}
    rc.delay_update(result_traceback='1')
    rc.delay_update(result_traceback=_('2'))
    rc.delay_update(result_traceback=_('3'), skip_if_already_set=True)
    assert rc.extra_update_fields == {'job_explanation': '1\n2', 'result_traceback': '1\n2'}


def test_duplicate_updates(mock_me):
    rc = RunnerCallback()
    rc.delay_update(job_explanation='really long summary...')
    rc.delay_update(job_explanation='really long summary...')
    rc.delay_update(job_explanation='really long summary...')
    assert rc.extra_update_fields == {'job_explanation': 'really long summary...'}


def test_special_ansible_runner_message(mock_me):
    rc = RunnerCallback()
    rc.delay_update(result_traceback='Traceback:\ngot an unexpected keyword argument\nFile: foo.py')
    rc.delay_update(result_traceback='Traceback:\ngot an unexpected keyword argument\nFile: bar.py')
    assert rc.get_delayed_update_fields().get('result_traceback') == (
        'Traceback:\ngot an unexpected keyword argument\nFile: foo.py\n'
        'Traceback:\ngot an unexpected keyword argument\nFile: bar.py\n'
        f'{ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE}'
    )


SAMPLE_ANSIBLE_DATA = {
    'installed_collections': {
        'ansible.builtin': {'version': '2.16.0'},
        'community.general': {'version': '8.0.0', 'host_query': 'SELECT * FROM hosts'},
    },
    'ansible_version': '2.16.0',
}


class TestTryLoadQueryFile:
    def test_loads_file_without_feature_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.flag_enabled', return_value=False):
                success, data = try_load_query_file(tmpdir)

            assert success is True
            assert data['ansible_version'] == '2.16.0'
            assert 'ansible.builtin' in data['installed_collections']

    def test_loads_file_with_feature_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.flag_enabled', return_value=True):
                success, data = try_load_query_file(tmpdir)

            assert success is True
            assert data == SAMPLE_ANSIBLE_DATA

    def test_returns_false_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            success, data = try_load_query_file(tmpdir)

            assert success is False
            assert data is None


class TestArtifactsHandler:
    def test_always_persists_metadata_when_flag_off(self, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.flag_enabled', return_value=False):
                rc.artifacts_handler(tmpdir)

        assert rc.extra_update_fields['installed_collections'] == SAMPLE_ANSIBLE_DATA['installed_collections']
        assert rc.extra_update_fields['ansible_version'] == '2.16.0'
        assert 'event_queries_processed' not in rc.extra_update_fields
        assert rc.artifacts_processed is True

    @mock.patch('awx.main.tasks.callback.EventQuery')
    def test_creates_event_queries_when_flag_on(self, mock_event_query, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.flag_enabled', return_value=True):
                rc.artifacts_handler(tmpdir)

        assert rc.extra_update_fields['installed_collections'] == SAMPLE_ANSIBLE_DATA['installed_collections']
        assert rc.extra_update_fields['ansible_version'] == '2.16.0'
        assert rc.extra_update_fields['event_queries_processed'] is False
        mock_event_query.assert_called_once()

    @mock.patch('awx.main.tasks.callback.EventQuery')
    def test_no_event_queries_when_flag_off(self, mock_event_query, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.flag_enabled', return_value=False):
                rc.artifacts_handler(tmpdir)

        mock_event_query.assert_not_called()

    def test_handles_missing_artifact_file(self, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch('awx.main.tasks.callback.flag_enabled', return_value=False):
                rc.artifacts_handler(tmpdir)

        assert 'installed_collections' not in rc.extra_update_fields
        assert 'ansible_version' not in rc.extra_update_fields
        assert rc.artifacts_processed is True
