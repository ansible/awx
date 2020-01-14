import pytest

from awx.api.versioning import reverse
from awx.main.models import AdHocCommand, AdHocCommandEvent, JobEvent


@pytest.mark.django_db
@pytest.mark.parametrize('truncate, expected', [
    (True, False),
    (False, True),
])
def test_job_events_sublist_truncation(get, organization_factory, job_template_factory, truncate, expected):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    job = jt.create_unified_job()
    JobEvent.create_from_data(job_id=job.pk, uuid='abc123', event='runner_on_start',
                              stdout='a' * 1025).save()

    url = reverse('api:job_job_events_list', kwargs={'pk': job.pk})
    if not truncate:
        url += '?no_truncate=1'

    response = get(url, user=objs.superusers.admin, expect=200)
    assert (len(response.data['results'][0]['stdout']) == 1025) == expected


@pytest.mark.django_db
@pytest.mark.parametrize('truncate, expected', [
    (True, False),
    (False, True),
])
def test_ad_hoc_events_sublist_truncation(get, organization_factory, job_template_factory, truncate, expected):
    objs = organization_factory("org", superusers=['admin'])
    adhoc = AdHocCommand()
    adhoc.save()
    AdHocCommandEvent.create_from_data(ad_hoc_command_id=adhoc.pk, uuid='abc123', event='runner_on_start',
                                       stdout='a' * 1025).save()

    url = reverse('api:ad_hoc_command_ad_hoc_command_events_list', kwargs={'pk': adhoc.pk})
    if not truncate:
        url += '?no_truncate=1'

    response = get(url, user=objs.superusers.admin, expect=200)
    assert (len(response.data['results'][0]['stdout']) == 1025) == expected
