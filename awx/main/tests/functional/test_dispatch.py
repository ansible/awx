import datetime
from unittest import mock
from django.utils.timezone import now as tz_now
import pytest

from awx.main.models import Job, WorkflowJob, Instance
from awx.main.dispatch import reaper
from dispatcherd.publish import task

'''
Prevent logger.<warn, debug, error> calls from triggering database operations
'''


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=mock.PropertyMock)
    m.return_value = []


def restricted(a, b):
    raise AssertionError("This code should not run because it isn't decorated with @task")


@task()
def add(a, b):
    return a + b


class BaseTask(object):
    def add(self, a, b):
        return add(a, b)


class Restricted(object):
    def run(self, a, b):
        raise AssertionError("This code should not run because it isn't decorated with @task")


@task()
class Adder(BaseTask):
    def run(self, a, b):
        return super(Adder, self).add(a, b)


@task(queue='hard-math')
def multiply(a, b):
    return a * b


yesterday = tz_now() - datetime.timedelta(days=1)
minute = tz_now() - datetime.timedelta(seconds=120)
now = tz_now()


@pytest.mark.django_db
class TestJobReaper(object):
    @pytest.mark.parametrize(
        'status, execution_node, controller_node, modified, fail',
        [
            ('running', '', '', None, False),  # running, not assigned to the instance
            ('running', 'awx', '', None, True),  # running, has the instance as its execution_node
            ('running', '', 'awx', None, True),  # running, has the instance as its controller_node
            ('waiting', '', '', None, False),  # waiting, not assigned to the instance
            ('waiting', 'awx', '', None, False),  # waiting, was edited less than a minute ago
            ('waiting', '', 'awx', None, False),  # waiting, was edited less than a minute ago
            ('waiting', 'awx', '', yesterday, False),  # waiting, managed by another node, ignore
            ('waiting', '', 'awx', yesterday, True),  # waiting, assigned to the controller_node, stale
        ],
    )
    def test_should_reap(self, status, fail, execution_node, controller_node, modified):
        i = Instance(hostname='awx')
        i.save()
        j = Job(
            status=status,
            execution_node=execution_node,
            controller_node=controller_node,
            start_args='SENSITIVE',
        )
        j.save()
        if modified:
            # we have to edit the modification time _without_ calling save()
            # (because .save() overwrites it to _now_)
            Job.objects.filter(id=j.id).update(modified=modified)
        reaper.reap(i)
        reaper.reap_waiting(i)
        job = Job.objects.first()
        if fail:
            assert job.status == 'failed'
            assert 'marked as failed' in job.job_explanation
            assert job.start_args == ''
        else:
            assert job.status == status

    @pytest.mark.parametrize(
        'excluded_uuids, fail, started',
        [
            (['abc123'], False, None),
            ([], False, None),
            ([], True, minute),
        ],
    )
    def test_do_not_reap_excluded_uuids(self, excluded_uuids, fail, started):
        """Modified Test to account for ref_time in reap()"""
        i = Instance(hostname='awx')
        i.save()
        j = Job(
            status='running',
            execution_node='awx',
            controller_node='',
            start_args='SENSITIVE',
            celery_task_id='abc123',
        )
        j.save()
        if started:
            Job.objects.filter(id=j.id).update(started=started)

        # if the UUID is excluded, don't reap it
        reaper.reap(i, excluded_uuids=excluded_uuids, ref_time=now)
        job = Job.objects.first()

        if fail:
            assert job.status == 'failed'
            assert 'marked as failed' in job.job_explanation
            assert job.start_args == ''
        else:
            assert job.status == 'running'

    def test_workflow_does_not_reap(self):
        i = Instance(hostname='awx')
        i.save()
        j = WorkflowJob(status='running', execution_node='awx')
        j.save()
        reaper.reap(i)

        assert WorkflowJob.objects.first().status == 'running'

    def test_should_not_reap_new(self):
        """
        This test is designed specifically to ensure that jobs that are launched after the dispatcher has provided a list of UUIDs aren't reaped.
        It is very racy and this test is designed with that in mind
        """
        i = Instance(hostname='awx')
        # ref_time is set to 10 seconds in the past to mimic someone launching a job in the heartbeat window.
        ref_time = tz_now() - datetime.timedelta(seconds=10)
        # creating job at current time
        job = Job.objects.create(status='running', controller_node=i.hostname)
        reaper.reap(i, ref_time=ref_time)
        # explictly refreshing from db to ensure up to date cache
        job.refresh_from_db()
        assert job.started > ref_time
        assert job.status == 'running'
        assert job.job_explanation == ''
