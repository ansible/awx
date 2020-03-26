from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from django.utils.timezone import now

from awx.main.models import Job


@pytest.mark.django_db
def test_job_wait_successful(run_module, admin_user):
    job = Job.objects.create(status='successful', started=now(), finished=now())
    result = run_module('tower_job_wait', dict(
        job_id=job.id
    ), admin_user)
    result.pop('invocation', None)
    assert result.pop('finished', '')[:10] == str(job.finished)[:10]
    assert result.pop('started', '')[:10] == str(job.started)[:10]
    assert result == {
        "status": "successful",
        "changed": False,
        "elapsed": str(job.elapsed),
        "id": job.id
    }


@pytest.mark.django_db
def test_job_wait_failed(run_module, admin_user):
    job = Job.objects.create(status='failed', started=now(), finished=now())
    result = run_module('tower_job_wait', dict(
        job_id=job.id
    ), admin_user)
    result.pop('invocation', None)
    assert result.pop('finished', '')[:10] == str(job.finished)[:10]
    assert result.pop('started', '')[:10] == str(job.started)[:10]
    assert result == {
        "status": "failed",
        "failed": True,
        "changed": False,
        "elapsed": str(job.elapsed),
        "id": job.id,
        "msg": "Job with id 1 failed"
    }


@pytest.mark.django_db
def test_job_wait_not_found(run_module, admin_user):
    result = run_module('tower_job_wait', dict(
        job_id=42
    ), admin_user)
    result.pop('invocation', None)
    assert result == {
        "failed": True,
        "msg": "Unable to wait on job 42; that ID does not exist in Tower."
    }
