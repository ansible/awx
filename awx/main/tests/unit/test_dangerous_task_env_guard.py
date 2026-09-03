# -*- coding: utf-8 -*-
import pytest
from unittest import mock

from rest_framework import serializers

from awx.main.models import ExecutionEnvironment
from awx.main.tasks import jobs

# These symbols only exist after the fix is applied.  A guarded import
# lets the module load so the runtime-guard tests (build_env /
# build_extra_vars_file) can still run and fail on assertions when
# the fix is reverted.
try:
    from awx.main.conf import _is_dangerous_task_env_key, jobs_validate
except ImportError:
    _is_dangerous_task_env_key = None
    jobs_validate = None

_guard_present = _is_dangerous_task_env_key is not None


# ---------------------------------------------------------------------------
# _is_dangerous_task_env_key — pure-function tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'key',
    [
        'LD_PRELOAD',
        'LD_LIBRARY_PATH',
        'ld_preload',
        'Ld_Preload',
        'DYLD_INSERT_LIBRARIES',
        'DYLD_LIBRARY_PATH',
        'dyld_insert_libraries',
        'PYTHONPATH',
        'PYTHONSTARTUP',
        'PYTHONHOME',
        'pythonpath',
        'PERL5OPT',
        'perl5opt',
    ],
)
def test_is_dangerous_task_env_key_rejects_dangerous(key):
    assert _guard_present, "fix not applied: _is_dangerous_task_env_key missing"
    assert _is_dangerous_task_env_key(key) is True


@pytest.mark.parametrize(
    'key',
    [
        'HTTP_PROXY',
        'HTTPS_PROXY',
        'NO_PROXY',
        'MY_CUSTOM_VAR',
        'ANSIBLE_CONFIG',
        'HOME',
        'PATH',
    ],
)
def test_is_dangerous_task_env_key_allows_safe(key):
    assert _guard_present, "fix not applied: _is_dangerous_task_env_key missing"
    assert _is_dangerous_task_env_key(key) is False


# ---------------------------------------------------------------------------
# jobs_validate — validator tests
# ---------------------------------------------------------------------------


class TestJobsValidate:

    def test_rejects_dangerous_key_in_awx_task_env(self):
        assert _guard_present, "fix not applied: jobs_validate missing"
        attrs = {'AWX_TASK_ENV': {'LD_PRELOAD': '/tmp/evil.so', 'HTTP_PROXY': 'http://proxy:8080'}}
        with pytest.raises(serializers.ValidationError) as exc_info:
            jobs_validate(None, attrs)
        assert 'LD_PRELOAD' in str(exc_info.value)

    def test_rejects_dangerous_key_in_galaxy_task_env(self):
        assert _guard_present, "fix not applied: jobs_validate missing"
        attrs = {'GALAXY_TASK_ENV': {'PYTHONPATH': '/tmp/evil', 'HTTP_PROXY': 'http://proxy:8080'}}
        with pytest.raises(serializers.ValidationError) as exc_info:
            jobs_validate(None, attrs)
        assert 'PYTHONPATH' in str(exc_info.value)

    def test_rejects_dangerous_keys_in_both_settings(self):
        assert _guard_present, "fix not applied: jobs_validate missing"
        attrs = {
            'AWX_TASK_ENV': {'LD_PRELOAD': '/tmp/evil.so'},
            'GALAXY_TASK_ENV': {'DYLD_INSERT_LIBRARIES': '/tmp/evil.dylib'},
        }
        with pytest.raises(serializers.ValidationError) as exc_info:
            jobs_validate(None, attrs)
        msg = str(exc_info.value)
        assert 'AWX_TASK_ENV' in msg
        assert 'GALAXY_TASK_ENV' in msg

    def test_permits_safe_keys(self):
        assert _guard_present, "fix not applied: jobs_validate missing"
        attrs = {
            'AWX_TASK_ENV': {'HTTP_PROXY': 'http://proxy:8080', 'MY_VAR': 'value'},
            'GALAXY_TASK_ENV': {'HTTPS_PROXY': 'http://proxy:8443'},
        }
        result = jobs_validate(None, attrs)
        assert result is attrs

    def test_permits_when_settings_not_in_attrs(self):
        assert _guard_present, "fix not applied: jobs_validate missing"
        attrs = {'SOME_OTHER_SETTING': 'value'}
        result = jobs_validate(None, attrs)
        assert result is attrs


# ---------------------------------------------------------------------------
# BaseTask.build_env — runtime guard on AWX_TASK_ENV
# ---------------------------------------------------------------------------


class TestBuildEnvFiltering:

    def _make_base_task(self):
        """Create a BaseTask without calling __init__ (avoids DB/settings)."""
        task = jobs.BaseTask.__new__(jobs.BaseTask)
        return task

    def _call_build_env(self, task_env_dict, tmp_path):
        """Call BaseTask.build_env with a mocked settings.AWX_TASK_ENV."""
        task = self._make_base_task()
        ee = ExecutionEnvironment(name='test-ee', description='test-ee', managed=True)
        instance = mock.MagicMock(spec=jobs.Job)
        instance.execution_environment = ee
        task.instance = instance

        private_data_dir = str(tmp_path)

        with mock.patch('awx.main.tasks.jobs.settings') as mock_settings:
            mock_settings.AWX_TASK_ENV = task_env_dict
            # dir(settings) returns ANSIBLE_* attrs; provide none
            mock_settings.__dir__ = mock.Mock(return_value=[])
            env = task.build_env(instance, private_data_dir)

        return env

    def test_filters_dangerous_keys_from_awx_task_env(self, tmp_path):
        task_env = {
            'LD_PRELOAD': '/tmp/evil.so',
            'PYTHONPATH': '/tmp/evil',
            'PERL5OPT': '-e system("evil")',
            'HTTP_PROXY': 'http://proxy:8080',
        }
        env = self._call_build_env(task_env, tmp_path)
        assert 'LD_PRELOAD' not in env
        assert 'PYTHONPATH' not in env
        assert 'PERL5OPT' not in env
        assert env['HTTP_PROXY'] == 'http://proxy:8080'

    def test_permits_safe_keys_in_awx_task_env(self, tmp_path):
        task_env = {
            'HTTP_PROXY': 'http://proxy:8080',
            'HTTPS_PROXY': 'http://proxy:8443',
            'MY_CUSTOM_VAR': 'hello',
        }
        env = self._call_build_env(task_env, tmp_path)
        assert env['HTTP_PROXY'] == 'http://proxy:8080'
        assert env['HTTPS_PROXY'] == 'http://proxy:8443'
        assert env['MY_CUSTOM_VAR'] == 'hello'


# ---------------------------------------------------------------------------
# RunProjectUpdate.build_extra_vars_file — runtime guard on GALAXY_TASK_ENV
# ---------------------------------------------------------------------------


class TestBuildExtraVarsFileFiltering:

    def _make_project_update_task(self):
        """Create a RunProjectUpdate without calling __init__."""
        task = jobs.RunProjectUpdate.__new__(jobs.RunProjectUpdate)
        return task

    def _mock_project_update(self, tmp_path):
        project_update = mock.MagicMock(spec=jobs.ProjectUpdate)
        project_update.scm_type = 'git'
        project_update.scm_url = 'https://github.com/example/repo.git'
        project_update.scm_branch = 'main'
        project_update.job_type = 'check'
        project_update.branch_override = False
        project_update.scm_clean = False
        project_update.scm_track_submodules = False
        project_update.scm_refspec = ''
        project_update.credential = None
        project_update.project.scm_revision = ''
        project_update.project.allow_override = False
        project_update.project.local_path = '/tmp/project'
        project_update.project.organization = None
        project_update.project.signature_validation_credential = None
        project_update.get_project_path.return_value = str(tmp_path / 'project')
        return project_update

    def test_filters_dangerous_keys_from_galaxy_task_env(self, tmp_path):
        """galaxy_task_env in the extra vars must not contain dangerous keys."""
        galaxy_env = {
            'LD_PRELOAD': '/tmp/evil.so',
            'PYTHONPATH': '/tmp/evil',
            'HTTP_PROXY': 'http://proxy:8080',
        }

        task = self._make_project_update_task()
        project_update = self._mock_project_update(tmp_path)

        # Capture what _write_extra_vars_file receives
        captured_vars = {}

        def capture_write(pdd, extra_vars):
            captured_vars.update(extra_vars)

        task._write_extra_vars_file = capture_write

        with mock.patch('awx.main.tasks.jobs.settings') as mock_settings:
            mock_settings.GALAXY_TASK_ENV = galaxy_env
            mock_settings.PROJECTS_ROOT = '/var/lib/awx/projects'
            mock_settings.INSIGHTS_URL_BASE = 'https://cloud.redhat.com'
            mock_settings.AWX_ROLES_ENABLED = False
            mock_settings.AWX_COLLECTIONS_ENABLED = False
            mock_settings.ALLOW_JINJA_IN_EXTRA_VARS = 'never'
            with mock.patch('awx.main.tasks.jobs.get_license', return_value={'license_type': 'enterprise'}):
                with mock.patch('awx.main.tasks.jobs.get_awx_version', return_value='1.0.0'):
                    task.build_extra_vars_file(project_update, str(tmp_path))

        galaxy_task_env = captured_vars['galaxy_task_env']
        assert 'LD_PRELOAD' not in galaxy_task_env
        assert 'PYTHONPATH' not in galaxy_task_env
        assert galaxy_task_env['HTTP_PROXY'] == 'http://proxy:8080'

    def test_permits_safe_keys_in_galaxy_task_env(self, tmp_path):
        """Safe keys in GALAXY_TASK_ENV must pass through to extra vars."""
        galaxy_env = {
            'HTTP_PROXY': 'http://proxy:8080',
            'HTTPS_PROXY': 'http://proxy:8443',
        }

        task = self._make_project_update_task()
        project_update = self._mock_project_update(tmp_path)

        captured_vars = {}

        def capture_write(pdd, extra_vars):
            captured_vars.update(extra_vars)

        task._write_extra_vars_file = capture_write

        with mock.patch('awx.main.tasks.jobs.settings') as mock_settings:
            mock_settings.GALAXY_TASK_ENV = galaxy_env
            mock_settings.PROJECTS_ROOT = '/var/lib/awx/projects'
            mock_settings.INSIGHTS_URL_BASE = 'https://cloud.redhat.com'
            mock_settings.AWX_ROLES_ENABLED = False
            mock_settings.AWX_COLLECTIONS_ENABLED = False
            mock_settings.ALLOW_JINJA_IN_EXTRA_VARS = 'never'
            with mock.patch('awx.main.tasks.jobs.get_license', return_value={'license_type': 'enterprise'}):
                with mock.patch('awx.main.tasks.jobs.get_awx_version', return_value='1.0.0'):
                    task.build_extra_vars_file(project_update, str(tmp_path))

        galaxy_task_env = captured_vars['galaxy_task_env']
        assert galaxy_task_env == {
            'HTTP_PROXY': 'http://proxy:8080',
            'HTTPS_PROXY': 'http://proxy:8443',
        }
