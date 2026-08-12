import logging
from datetime import timedelta
from unittest import mock

import pytest

from django.utils.timezone import now

from awx.main.management.commands.cleanup_jobs import Command
from awx.main.models import Job


@pytest.fixture(autouse=True)
def no_postgres_only_sql():
    """cleanup_jobs reaches PostgreSQL-only SQL on either side of the batch
    loop: _pre_delete_job_host_summaries uses ANY(%s), and
    has_unpartitioned_table reads pg_tables. The test database is SQLite, so
    stub both out and let the batch loop itself run. The raw statements are
    covered in awx/main/tests/unit/commands/test_cleanup_jobs.py."""
    with mock.patch('awx.main.management.commands.cleanup_jobs._pre_delete_job_host_summaries'):
        with mock.patch.object(Command, 'has_unpartitioned_table', return_value=False):
            yield


@pytest.fixture
def old_jobs(inventory):
    """Six finished jobs old enough for cleanup to pick up."""
    created = now() - timedelta(days=400)
    jobs = []
    for i in range(6):
        job = Job.objects.create(name='old-job-%d' % i, inventory=inventory, status='successful')
        Job.objects.filter(pk=job.pk).update(created=created)
        jobs.append(job)
    return jobs


def _command(batch_size):
    command = Command()
    command.logger = logging.getLogger('awx.main.commands.cleanup_jobs')
    command.cutoff = now() - timedelta(days=1)
    command.dry_run = False
    command.batch_size = batch_size
    return command


@pytest.mark.django_db
def test_cleanup_jobs_with_a_gap_in_the_id_range(old_jobs):
    """A batch window covering only ids whose jobs are already gone must not fail.

    Job shares the UnifiedJob id sequence with project updates, inventory
    updates and workflow jobs, so a window of ids holding no deletable Job is
    routine rather than exceptional.
    """
    Job.objects.filter(pk__in=[old_jobs[2].pk, old_jobs[3].pk]).delete()
    expected = Job.objects.filter(pk__in=[job.pk for job in old_jobs]).count()

    skipped, deleted = _command(batch_size=1).cleanup_jobs()

    assert deleted == expected
    assert not Job.objects.filter(pk__in=[job.pk for job in old_jobs]).exists()


@pytest.mark.django_db
def test_cleanup_jobs_when_the_id_span_is_a_multiple_of_the_batch_size(old_jobs):
    """Batch windows overlap on their boundary id, so the highest job can be
    swept up by the previous window and leave the final window empty."""
    first, last = old_jobs[0].pk, old_jobs[-1].pk
    batch_size = last - first
    expected = len(old_jobs)

    skipped, deleted = _command(batch_size=batch_size).cleanup_jobs()

    assert deleted == expected
    assert not Job.objects.filter(pk__in=[job.pk for job in old_jobs]).exists()


@pytest.mark.django_db
def test_cleanup_jobs_deletes_every_old_job(old_jobs):
    skipped, deleted = _command(batch_size=100000).cleanup_jobs()

    assert deleted == len(old_jobs)
    assert not Job.objects.filter(pk__in=[job.pk for job in old_jobs]).exists()
