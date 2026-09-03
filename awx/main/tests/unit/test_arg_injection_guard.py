"""
Regression tests for argument injection guards on scm_branch and scm_refspec.

The fix rejects values starting with ``-`` (after stripping leading whitespace)
at two layers:

  1. ``ProjectOptionsSerializer.validate`` — API-level validation
  2. ``RunProjectUpdate.build_extra_vars_file`` — task-level defense-in-depth
"""

import pytest
from unittest import mock

from rest_framework import serializers as drf_serializers

from awx.api.serializers import ProjectOptionsSerializer
from awx.main.models import Organization, Project, ProjectUpdate
from awx.main.tasks import jobs
from awx.main.utils.licensing import Licenser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def serializer_validate_deps():
    """Isolate ProjectOptionsSerializer.validate from DB / model internals."""
    with mock.patch.object(Project, 'get_local_path_choices', return_value=[]):
        with mock.patch(
            'awx.api.serializers.BaseSerializer.validate',
            lambda self, attrs: attrs,
        ):
            yield


@pytest.fixture
def private_data_dir(tmp_path):
    pdd = tmp_path / 'awx_pdd'
    pdd.mkdir()
    for sub in ('inventory', 'env'):
        (pdd / sub).mkdir()
    return str(pdd)


@pytest.fixture
def patch_organization():
    _creds = []
    creds_mock = mock.Mock(
        **{
            'all': lambda: _creds,
            'add': _creds.append,
            'exists': lambda: len(_creds) > 0,
            'spec_set': ['all', 'add', 'exists'],
        }
    )
    with mock.patch.object(Organization, 'galaxy_credentials', creds_mock):
        yield


@pytest.fixture
def project_update(execution_environment):
    org = Organization(pk=1)
    proj = Project(pk=1, organization=org)
    pu = ProjectUpdate(pk=1, project=proj, scm_type='git')
    pu.websocket_emit_status = mock.Mock()
    pu.execution_environment = execution_environment
    return pu


# ---------------------------------------------------------------------------
# Serializer-layer tests  (ProjectOptionsSerializer.validate)
# ---------------------------------------------------------------------------


class TestProjectOptionsSerializerArgInjection:
    """scm_branch / scm_refspec starting with '-' must raise ValidationError."""

    @pytest.mark.parametrize(
        'branch',
        [
            '--pathspec-from-file=/etc/passwd',
            '-x',
            ' --pathspec-from-file=/etc/passwd',
        ],
    )
    def test_scm_branch_dash_rejected(
        self,
        serializer_validate_deps,
        branch,
    ):
        serializer = ProjectOptionsSerializer()
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({'scm_type': 'git', 'scm_branch': branch})
        assert 'scm_branch' in exc_info.value.detail

    def test_scm_branch_normal_allowed(self, serializer_validate_deps):
        serializer = ProjectOptionsSerializer()
        result = serializer.validate(
            {'scm_type': 'git', 'scm_branch': 'main'},
        )
        assert result['scm_branch'] == 'main'

    @pytest.mark.parametrize(
        'refspec',
        [
            '-x',
            '--upload-pack=malicious',
            ' -x',
        ],
    )
    def test_scm_refspec_dash_rejected(
        self,
        serializer_validate_deps,
        refspec,
    ):
        serializer = ProjectOptionsSerializer()
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            serializer.validate({'scm_type': 'git', 'scm_refspec': refspec})
        assert 'scm_refspec' in exc_info.value.detail

    def test_scm_refspec_normal_allowed(self, serializer_validate_deps):
        serializer = ProjectOptionsSerializer()
        result = serializer.validate(
            {
                'scm_type': 'git',
                'scm_refspec': '+refs/heads/*:refs/remotes/origin/*',
            }
        )
        assert result['scm_refspec'] == '+refs/heads/*:refs/remotes/origin/*'


# ---------------------------------------------------------------------------
# Task-layer tests  (RunProjectUpdate.build_extra_vars_file)
# ---------------------------------------------------------------------------


class TestBuildExtraVarsArgInjection:
    """build_extra_vars_file raises RuntimeError for dash-prefixed values."""

    def test_scm_branch_dash_rejected(
        self,
        patch_organization,
        private_data_dir,
        project_update,
        mock_me,
    ):
        project_update.scm_branch = '--pathspec-from-file=/etc/passwd'
        task = jobs.RunProjectUpdate()
        task.instance = project_update
        with mock.patch.object(Licenser, 'validate', lambda *a, **kw: {}):
            with pytest.raises(
                RuntimeError,
                match='Rejected scm_branch',
            ):
                task.build_extra_vars_file(project_update, private_data_dir)

    def test_scm_branch_normal_allowed(
        self,
        patch_organization,
        private_data_dir,
        project_update,
        mock_me,
    ):
        class Capture(jobs.RunProjectUpdate):
            captured = {}

            def _write_extra_vars_file(self, pdd, extra_vars, *a):
                self.captured = extra_vars

        project_update.scm_branch = 'main'
        task = Capture()
        task.instance = project_update
        with mock.patch.object(Licenser, 'validate', lambda *a, **kw: {}):
            task.build_extra_vars_file(project_update, private_data_dir)
        assert task.captured['scm_branch'] == 'main'

    def test_scm_refspec_dash_rejected(
        self,
        patch_organization,
        private_data_dir,
        project_update,
        mock_me,
    ):
        project_update.scm_refspec = '-some-malicious-flag'
        task = jobs.RunProjectUpdate()
        task.instance = project_update
        with mock.patch.object(Licenser, 'validate', lambda *a, **kw: {}):
            with pytest.raises(
                RuntimeError,
                match='Rejected scm_refspec',
            ):
                task.build_extra_vars_file(project_update, private_data_dir)

    def test_scm_refspec_normal_allowed(
        self,
        patch_organization,
        private_data_dir,
        project_update,
        mock_me,
    ):
        class Capture(jobs.RunProjectUpdate):
            captured = {}

            def _write_extra_vars_file(self, pdd, extra_vars, *a):
                self.captured = extra_vars

        project_update.scm_refspec = 'refs/pull/*/head:refs/remotes/origin/pr/*'
        task = Capture()
        task.instance = project_update
        with mock.patch.object(Licenser, 'validate', lambda *a, **kw: {}):
            task.build_extra_vars_file(project_update, private_data_dir)
        assert task.captured['scm_refspec'] == 'refs/pull/*/head:refs/remotes/origin/pr/*'
