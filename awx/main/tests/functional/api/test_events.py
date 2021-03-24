import pytest
from unittest import mock

from awx.api.versioning import reverse
from awx.main.models import AdHocCommand, AdHocCommandEvent, JobEvent
from awx.main.models import Job


# Job.created_or_epoch is used to help retrieve events that were
# created before job event tables were partitioned.
# This test can safely behave as if all job events were created
# after the migration, in which case Job.created_or_epoch == Job.created
@mock.patch('awx.main.models.Job.created_or_epoch', Job.created)
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


# Job.created_or_epoch is used to help retrieve events that were
# created before job event tables were partitioned.
# This test can safely behave as if all job events were created
# after the migration, in which case Job.created_or_epoch == Job.created
@mock.patch('awx.main.models.ad_hoc_commands.AdHocCommand.created_or_epoch', Job.created)
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
