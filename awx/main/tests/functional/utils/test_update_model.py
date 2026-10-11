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
def test_abort_signal_stops_the_retry(normal_job, mocker):
    mocker.patch.object(Job.objects, 'get', side_effect=DatabaseError)
    mocker.patch('awx.main.utils.update_model.time.sleep')
    mocker.patch('awx.main.utils.update_model.signal_callback', return_value=True)
    with pytest.raises(RuntimeError, match='abort signal'):
        update_model(Job, normal_job.pk)


@pytest.mark.django_db
def test_retry_keeps_the_owner_fence(normal_job, mocker):
    Job.objects.filter(pk=normal_job.pk).update(celery_task_id='adoption-task')
    write = mocker.patch('awx.main.utils.update_model._write_fields', side_effect=[DatabaseError, normal_job])
    mocker.patch('awx.main.utils.update_model.time.sleep')

    assert update_model(Job, normal_job.pk, owner_task_id='adoption-task', status='failed') is normal_job
    assert write.call_args_list[1].args == (Job, normal_job.pk, True, 'adoption-task', {'status': 'failed'})
