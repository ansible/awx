import pytest

from django.db import DatabaseError

from awx.main.models.jobs import Job
from awx.main.utils.update_model import update_model


@pytest.fixture
def normal_job(deploy_jobtemplate):
    return deploy_jobtemplate.create_unified_job()


class NewException(Exception):
    pass


@pytest.mark.django_db
def test_normal_get(normal_job):
    mod_job = Job.objects.get(pk=normal_job.id)
    mod_job.job_explanation = 'foobar'
    mod_job.save(update_fields=['job_explanation'])
    new_job = update_model(Job, normal_job.pk)
    assert new_job.job_explanation == 'foobar'


@pytest.mark.django_db
def test_exception(normal_job, mocker):
    mocker.patch.object(Job.objects, 'get', side_effect=DatabaseError)
    mocker.patch('awx.main.utils.update_model.time.sleep')
    with pytest.raises(DatabaseError):
        update_model(Job, normal_job.pk)


@pytest.mark.django_db
def test_unknown_exception(normal_job, mocker):
    mocker.patch.object(Job.objects, 'get', side_effect=NewException)
    mocker.patch('awx.main.utils.update_model.time.sleep')
    with pytest.raises(NewException):
        update_model(Job, normal_job.pk)


@pytest.mark.django_db
def test_deleted_job(normal_job):
    job_pk = normal_job.pk
    normal_job.delete()
    assert update_model(Job, job_pk) is None


@pytest.mark.django_db
def test_required_status_matches_proceeds(normal_job):
    """_required_status equal to the current status: update proceeds normally."""
    Job.objects.filter(pk=normal_job.pk).update(status='running')
    result = update_model(Job, normal_job.pk, select_for_update=True, _required_status='running', status='successful')
    assert result is not None
    assert result.status == 'successful'


@pytest.mark.django_db
def test_required_status_mismatch_returns_none(normal_job):
    """_required_status that does not match: update is skipped and None is returned.
    This is the double-finalization fence: a second controller sees status != 'running'
    inside the row lock and bails without overwriting the first controller's result."""
    Job.objects.filter(pk=normal_job.pk).update(status='successful')
    result = update_model(Job, normal_job.pk, select_for_update=True, _required_status='running', status='failed')
    assert result is None
    # The first controller's status must be preserved.
    assert Job.objects.get(pk=normal_job.pk).status == 'successful'
