import json
import os
import tempfile
from collections import deque
from unittest import mock

import pytest

from awx.main.tasks.callback import RunnerCallback, RunnerCallbackForProjectUpdate, try_load_query_file
from awx.main.constants import ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE
from awx.main.redact import UriCleaner

from django.utils.translation import gettext_lazy as _

SCM_USERNAME = 'scmuser'
SCM_PASSWORD = 'scmpass'
SCM_URL = f'https://{SCM_USERNAME}:{SCM_PASSWORD}@git.example.com/org/repo.git'


def _project_update_callback():
    cb = RunnerCallbackForProjectUpdate()
    cb.instance = mock.Mock(id=1)
    cb.event_data_key = 'project_update_id'
    cb.wrapup_event_type = 'playbook_on_stats'
    cb.job_created = '2026-01-01T00:00:00Z'
    cb.parent_workflow_job_id = None
    cb.host_map = {}
    cb.recent_event_timings = deque(maxlen=0)
    cb.dispatcher = mock.Mock()
    cb.guid = 'test-guid'
    return cb


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
    def test_loads_file_when_indirect_node_counting_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            success, data = try_load_query_file(tmpdir)

            assert success is True
            assert data['ansible_version'] == '2.16.0'
            assert 'ansible.builtin' in data['installed_collections']

    def test_loads_file_when_indirect_node_counting_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            success, data = try_load_query_file(tmpdir)

            assert success is True
            assert data == SAMPLE_ANSIBLE_DATA

    def test_returns_false_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            success, data = try_load_query_file(tmpdir)

            assert success is False
            assert data is None


class TestArtifactsHandler:
    def test_always_persists_metadata_when_indirect_node_counting_disabled(self, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.settings.INDIRECT_NODE_COUNTING_ENABLED', False):
                rc.artifacts_handler(tmpdir)

        assert rc.extra_update_fields['installed_collections'] == SAMPLE_ANSIBLE_DATA['installed_collections']
        assert rc.extra_update_fields['ansible_version'] == '2.16.0'
        assert 'event_queries_processed' not in rc.extra_update_fields
        assert rc.artifacts_processed is True

    @mock.patch('awx.main.tasks.callback.EventQuery')
    def test_creates_event_queries_when_indirect_node_counting_enabled(self, mock_event_query, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.settings.INDIRECT_NODE_COUNTING_ENABLED', True):
                rc.artifacts_handler(tmpdir)

        assert rc.extra_update_fields['installed_collections'] == SAMPLE_ANSIBLE_DATA['installed_collections']
        assert rc.extra_update_fields['ansible_version'] == '2.16.0'
        assert rc.extra_update_fields['event_queries_processed'] is False
        mock_event_query.assert_called_once()

    @mock.patch('awx.main.tasks.callback.EventQuery')
    def test_no_event_queries_when_indirect_node_counting_disabled(self, mock_event_query, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'ansible_data.json')
            with open(path, 'w') as f:
                json.dump(SAMPLE_ANSIBLE_DATA, f)

            with mock.patch('awx.main.tasks.callback.settings.INDIRECT_NODE_COUNTING_ENABLED', False):
                rc.artifacts_handler(tmpdir)

        mock_event_query.assert_not_called()

    def test_handles_missing_artifact_file(self, mock_me):
        rc = RunnerCallback()
        with tempfile.TemporaryDirectory() as tmpdir:
            rc.artifacts_handler(tmpdir)

        assert 'installed_collections' not in rc.extra_update_fields
        assert 'ansible_version' not in rc.extra_update_fields
        assert rc.artifacts_processed is True


@pytest.mark.parametrize('task_action', ['git', 'svn', 'ansible.builtin.git', 'ansible.builtin.svn'])
def test_project_update_redacts_scm_credentials(task_action, mock_me):
    """Git/SVN events redact HTTP basic-auth from dispatched project-update payloads."""
    cb = _project_update_callback()
    cb.event_handler(
        {
            'event': 'runner_on_failed',
            'stdout': f'failed: {SCM_URL}',
            'event_data': {'task_action': task_action, 'res': {'msg': f'Failed to clone {SCM_URL}'}},
        }
    )
    dispatched = json.dumps(cb.dispatcher.dispatch.call_args[0][0])
    assert SCM_USERNAME not in dispatched
    assert SCM_PASSWORD not in dispatched
    assert UriCleaner.REPLACE_STR in dispatched


def test_project_update_skips_scm_redaction_without_task_action(mock_me):
    """Omitted event_data has no task_action, so UriCleaner never runs on SCM stdout."""
    cb = _project_update_callback()
    cb.event_handler({'event': 'runner_on_failed', 'stdout': f'failed: {SCM_URL}', 'event_data': {}})
    dispatched = cb.dispatcher.dispatch.call_args[0][0]
    assert SCM_PASSWORD in dispatched['stdout']


@pytest.mark.parametrize('task_action', ['set_fact', 'ansible.builtin.set_fact'])
def test_project_update_captures_scm_version(task_action, mock_me):
    """Successful set_fact events still populate playbook_new_revision."""
    cb = _project_update_callback()
    cb.event_handler(
        {
            'event': 'runner_on_ok',
            'event_data': {'task_action': task_action, 'res': {'ansible_facts': {'scm_version': 'abc123def'}}},
        }
    )
    assert cb.playbook_new_revision == 'abc123def'


def test_project_update_skips_revision_capture_without_task_action(mock_me):
    """Omitted successful-event payloads never expose scm_version to the callback."""
    cb = _project_update_callback()
    cb.event_handler({'event': 'runner_on_ok', 'event_data': {}})
    assert cb.playbook_new_revision is None
