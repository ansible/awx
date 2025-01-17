import pytest
import os

from awx.main.tasks.jobs import RunJob
from awx.main.models import Job


@pytest.fixture
def scm_revision_file(tmpdir_factory):
    # Returns path to temporary testing revision file
    revision_file = tmpdir_factory.mktemp('revisions').join('revision.txt')
    with open(str(revision_file), 'w') as f:
        f.write('1234567890123456789012345678901234567890')
    return os.path.join(revision_file.dirname, 'revision.txt')


@pytest.mark.django_db
def test_does_not_run_reaped_job(mocker, mock_me):
    job = Job.objects.create(status='failed', job_explanation='This job has been reaped.')
    mock_run = mocker.patch('awx.main.tasks.jobs.ansible_runner.interface.run')
    try:
        RunJob().run(job.id)
    except Exception:
        pass
    job.refresh_from_db()
    assert job.status == 'failed'
    mock_run.assert_not_called()
