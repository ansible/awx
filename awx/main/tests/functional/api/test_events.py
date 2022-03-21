import pytest

from awx.api.versioning import reverse
from awx.main.models import AdHocCommand, AdHocCommandEvent, JobEvent


@pytest.mark.django_db
@pytest.mark.parametrize(
    'truncate, expected',
    [
        (True, False),
        (False, True),
    ],
)
def test_job_events_sublist_truncation(get, organization_factory, job_template_factory, truncate, expected):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, inventory='test_inv', project='test_proj').job_template
    job = jt.create_unified_job()
    JobEvent.create_from_data(job_id=job.pk, uuid='abc123', event='runner_on_start', stdout='a' * 1025, job_created=job.created).save()

    url = reverse('api:job_job_events_list', kwargs={'pk': job.pk})
    if not truncate:
        url += '?no_truncate=1'

    response = get(url, user=objs.superusers.admin, expect=200)
    assert (len(response.data['results'][0]['stdout']) == 1025) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    'truncate, expected',
    [
        (True, False),
        (False, True),
    ],
)
def test_ad_hoc_events_sublist_truncation(get, organization_factory, job_template_factory, truncate, expected):
    objs = organization_factory("org", superusers=['admin'])
    adhoc = AdHocCommand()
    adhoc.save()
    AdHocCommandEvent.create_from_data(ad_hoc_command_id=adhoc.pk, uuid='abc123', event='runner_on_start', stdout='a' * 1025, job_created=adhoc.created).save()

    url = reverse('api:ad_hoc_command_ad_hoc_command_events_list', kwargs={'pk': adhoc.pk})
    if not truncate:
        url += '?no_truncate=1'

    response = get(url, user=objs.superusers.admin, expect=200)
    assert (len(response.data['results'][0]['stdout']) == 1025) == expected


@pytest.mark.django_db
def test_job_job_events_children_summary(get, organization_factory, job_template_factory):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, inventory='test_inv', project='test_proj').job_template
    job = jt.create_unified_job()
    url = reverse('api:job_job_events_children_summary', kwargs={'pk': job.pk})
    response = get(url, user=objs.superusers.admin, expect=200)
    assert response.data["event_processing_finished"] == False
    '''
    E1
      E2
        E3
        E4 (verbose)
      E5
    '''
    JobEvent.create_from_data(
        job_id=job.pk, uuid='uuid1', parent_uuid='', event="playbook_on_start", counter=1, stdout='a' * 1024, job_created=job.created
    ).save()
    JobEvent.create_from_data(
        job_id=job.pk, uuid='uuid2', parent_uuid='uuid1', event="playbook_on_play_start", counter=2, stdout='a' * 1024, job_created=job.created
    ).save()
    JobEvent.create_from_data(
        job_id=job.pk, uuid='uuid3', parent_uuid='uuid2', event="runner_on_start", counter=3, stdout='a' * 1024, job_created=job.created
    ).save()
    JobEvent.create_from_data(job_id=job.pk, uuid='uuid4', parent_uuid='', event='verbose', counter=4, stdout='a' * 1024, job_created=job.created).save()
    JobEvent.create_from_data(
        job_id=job.pk, uuid='uuid5', parent_uuid='uuid1', event="playbook_on_task_start", counter=5, stdout='a' * 1024, job_created=job.created
    ).save()
    job.emitted_events = job.get_event_queryset().count()
    job.status = "successful"
    job.save()
    url = reverse('api:job_job_events_children_summary', kwargs={'pk': job.pk})
    response = get(url, user=objs.superusers.admin, expect=200)
    assert response.data["children_summary"] == {1: {"rowNumber": 0, "numChildren": 4}, 2: {"rowNumber": 1, "numChildren": 2}}
    assert response.data["meta_event_nested_uuid"] == {4: "uuid2"}
    assert response.data["event_processing_finished"] == True
