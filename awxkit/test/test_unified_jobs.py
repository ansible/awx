from unittest import mock

import pytest

from awxkit.api.pages.unified_jobs import UnifiedJob


def _make_job(job_id, job_args):
    """Create a minimal UnifiedJob mock with the given id and job_args."""
    job = mock.MagicMock(spec=UnifiedJob)
    job.id = job_id
    job.get = mock.MagicMock()
    type(job).job_args = mock.PropertyMock(return_value=job_args)
    type(job).controller_dir = UnifiedJob.controller_dir
    return job


class TestControllerDir:
    def test_traditional_path(self):
        job = _make_job(4387, ['podman', 'run', '-v', '/tmp/awx_4387_qv4aqn_8/:/runner/:Z', '--name', 'test'])
        assert job.controller_dir == '/tmp/awx_4387_qv4aqn_8/'

    def test_containerized_path(self):
        job = _make_job(
            4387,
            [
                'podman',
                'run',
                '-v',
                '/home/ansible/aap/controller/data/job_execution/awx_4387_qv4aqn_8/:/runner/:Z',
                '--name',
                'test',
            ],
        )
        assert job.controller_dir == '/home/ansible/aap/controller/data/job_execution/awx_4387_qv4aqn_8/'

    def test_no_false_match_on_similar_id(self):
        job = _make_job(1, ['podman', 'run', '-v', '/tmp/awx_10_abc/:/runner/:Z', '--name', 'test'])
        with pytest.raises(RuntimeError, match='Could not find a controller private_data_dir'):
            _ = job.controller_dir

    def test_exact_segment_match(self):
        job = _make_job(1, ['podman', 'run', '-v', '/tmp/awx_1/:/runner/:Z', '--name', 'test'])
        assert job.controller_dir == '/tmp/awx_1/'

    def test_segment_with_suffix(self):
        job = _make_job(1, ['podman', 'run', '-v', '/tmp/awx_1_abc/:/runner/:Z', '--name', 'test'])
        assert job.controller_dir == '/tmp/awx_1_abc/'

    def test_no_volume_mounts_raises(self):
        job = _make_job(99, ['podman', 'run', '--name', 'test'])
        with pytest.raises(RuntimeError, match='Could not find a controller private_data_dir'):
            _ = job.controller_dir

    def test_multiple_volumes_picks_correct(self):
        job = _make_job(
            42,
            [
                'podman',
                'run',
                '-v',
                '/etc/pki:/etc/pki:O',
                '-v',
                '/home/ansible/aap/controller/data/job_execution/awx_42_xyz/:/runner/:Z',
                '-v',
                '/usr/share/pki:/usr/share/pki:O',
                '--name',
                'test',
            ],
        )
        assert job.controller_dir == '/home/ansible/aap/controller/data/job_execution/awx_42_xyz/'
