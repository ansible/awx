import pytest
from datetime import datetime, timedelta
from pytz import timezone
from collections import OrderedDict

from django.db.models.deletion import Collector, SET_NULL, CASCADE
from django.core.management import call_command

from awx.main.management.commands.deletion import AWXCollector
from awx.main.models import (
    JobTemplate, User, Job, JobEvent, Notification,
    WorkflowJobNode, JobHostSummary
)


@pytest.fixture
def setup_environment(inventory, project, machine_credential, host, notification_template, label):
    '''
    Create old jobs and new jobs, with various other objects to hit the
    related fields of Jobs. This makes sure on_delete() effects are tested
    properly.
    '''
    old_jobs = []
    new_jobs = []
    days = 10
    days_str = str(days)

    jt = JobTemplate.objects.create(name='testjt', inventory=inventory, project=project)
    jt.credentials.add(machine_credential)
    jt_user = User.objects.create(username='jobtemplateuser')
    jt.execute_role.members.add(jt_user)

    notification = Notification()
    notification.notification_template = notification_template
    notification.save()

    for i in range(3):
        job1 = jt.create_job()
        job1.created =datetime.now(tz=timezone('UTC'))
        job1.save()
        # create jobs with current time
        JobEvent.create_from_data(job_id=job1.pk, uuid='abc123', event='runner_on_start',
                                  stdout='a' * 1025).save()
        new_jobs.append(job1)

        job2 = jt.create_job()
        # create jobs 10 days ago
        job2.created = datetime.now(tz=timezone('UTC')) - timedelta(days=days)
        job2.save()
        job2.dependent_jobs.add(job1)
        JobEvent.create_from_data(job_id=job2.pk, uuid='abc123', event='runner_on_start',
                                  stdout='a' * 1025).save()
        old_jobs.append(job2)

    jt.last_job = job2
    jt.current_job = job2
    jt.save()
    host.last_job = job2
    host.save()
    notification.unifiedjob_notifications.add(job2)
    label.unifiedjob_labels.add(job2)
    jn = WorkflowJobNode.objects.create(job=job2)
    jn.save()
    jh = JobHostSummary.objects.create(job=job2)
    jh.save()

    return (old_jobs, new_jobs, days_str)


@pytest.mark.django_db
def test_cleanup_jobs(setup_environment):
    (old_jobs, new_jobs, days_str) = setup_environment

    # related_fields
    related = [f for f in Job._meta.get_fields(include_hidden=True)
               if f.auto_created and not
               f.concrete and
               (f.one_to_one or f.one_to_many)]

    job = old_jobs[-1] # last job

    # gather related objects for job
    related_should_be_removed = {}
    related_should_be_null = {}
    for r in related:
        qs = r.related_model._base_manager.using('default').filter(
            **{"%s__in" % r.field.name: [job.pk]}
        )
        if qs.exists():
            if r.field.remote_field.on_delete == CASCADE:
                related_should_be_removed[qs.model] = set(qs.values_list('pk', flat=True))
            if r.field.remote_field.on_delete == SET_NULL:
                related_should_be_null[(qs.model,r.field.name)] = set(qs.values_list('pk', flat=True))

    assert related_should_be_removed
    assert related_should_be_null

    call_command('cleanup_jobs', '--days', days_str)
    # make sure old jobs are removed
    assert not Job.objects.filter(pk__in=[obj.pk for obj in old_jobs]).exists()

    # make sure new jobs are untouched
    assert len(new_jobs) == Job.objects.filter(pk__in=[obj.pk for obj in new_jobs]).count()

    # make sure related objects are destroyed or set to NULL (none)
    for model, values in related_should_be_removed.items():
        assert not model.objects.filter(pk__in=values).exists()

    for (model,fieldname), values in related_should_be_null.items():
        for v in values:
            assert not getattr(model.objects.get(pk=v), fieldname)


@pytest.mark.django_db
def test_awxcollector(setup_environment):
    '''
    Efforts to improve the performance of cleanup_jobs involved
    sub-classing the django Collector class. This unit test will
    check for parity between the django Collector and the modified
    AWXCollector class. AWXCollector is used in cleanup_jobs to
    bulk-delete old jobs from the database.

    Specifically, Collector has four dictionaries to check:
    .dependencies, .data, .fast_deletes, and .field_updates

    These tests will convert each dictionary from AWXCollector
    (after running .collect on jobs), from querysets to sets of
    objects. The final result should be a dictionary that is
    equivalent to django's Collector.
    '''

    (old_jobs, new_jobs, days_str) = setup_environment
    collector = Collector('default')
    collector.collect(old_jobs)

    awx_col = AWXCollector('default')
    # awx_col accepts a queryset as input
    awx_col.collect(Job.objects.filter(pk__in=[obj.pk for obj in old_jobs]))

    # check that dependencies are the same
    assert awx_col.dependencies == collector.dependencies

    # check that objects to delete are the same
    awx_del_dict = OrderedDict()
    for model, instances in awx_col.data.items():
        awx_del_dict.setdefault(model, set())
        for inst in instances:
            # .update() will put each object in a queryset into the set
            awx_del_dict[model].update(inst)
    assert awx_del_dict == collector.data

    # check that field updates are the same
    awx_del_dict = OrderedDict()
    for model, instances_for_fieldvalues in awx_col.field_updates.items():
        awx_del_dict.setdefault(model, {})
        for (field, value), instances in instances_for_fieldvalues.items():
            awx_del_dict[model].setdefault((field,value), set())
            for inst in instances:
                awx_del_dict[model][(field,value)].update(inst)

    # collector field updates don't use the base (polymorphic parent) model, e.g.
    # it will use JobTemplate instead of UnifiedJobTemplate. Therefore,
    # we need to rebuild the dictionary and grab the model from the field
    collector_del_dict = OrderedDict()
    for model, instances_for_fieldvalues in collector.field_updates.items():
        for (field,value), instances in instances_for_fieldvalues.items():
            collector_del_dict.setdefault(field.model, {})
            collector_del_dict[field.model][(field, value)] = collector.field_updates[model][(field,value)]
    assert awx_del_dict == collector_del_dict

    # check that fast deletes are the same
    collector_fast_deletes = set()
    for q in collector.fast_deletes:
        collector_fast_deletes.update(q)

    awx_col_fast_deletes = set()
    for q in awx_col.fast_deletes:
        awx_col_fast_deletes.update(q)
    assert collector_fast_deletes == awx_col_fast_deletes
