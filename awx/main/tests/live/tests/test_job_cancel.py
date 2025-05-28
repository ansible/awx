import time

from awx.api.versioning import reverse
from awx.main.models import Job

from awx.main.tests.live.tests.conftest import wait_for_events


def test_cancel_and_delete_job(live_tmp_folder, run_job_from_playbook, post, delete, admin):
    res = run_job_from_playbook('test_cancel_and_delete_job', 'sleep.yml', scm_url=f'file://{live_tmp_folder}/debug', wait=False)
    job = res['job']
    assert job.status == 'pending'

    # Wait for first event so that we can be sure the job is in-progress first
    start = time.time()
    timeout = 10.0
    while not job.job_events.exists():
        time.sleep(0.2)
        if time.time() - start > timeout:
            assert False, f'Did not receive first event for job_id={job.id} in {timeout} seconds'

    # Now cancel the job
    url = reverse("api:job_cancel", kwargs={'pk': job.pk})
    post(url, user=admin, expect=202)

    # Job status should change to expected status before infinity
    start = time.time()
    timeout = 5.0
    job.refresh_from_db()
    while job.status != 'canceled':
        time.sleep(0.05)
        job.refresh_from_db(fields=['status'])
        if time.time() - start > timeout:
            assert False, f'job_id={job.id} still status={job.status} after {timeout} seconds'

    wait_for_events(job)
    url = reverse("api:job_detail", kwargs={'pk': job.pk})
    delete(url, user=admin, expect=204)

    assert not Job.objects.filter(id=job.id).exists()
