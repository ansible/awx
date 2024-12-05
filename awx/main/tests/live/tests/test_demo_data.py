import time

from awx.api.versioning import reverse

from awx.main.models import JobTemplate, Job


def wait_to_leave_status(job, status, timeout=25):
    """Wait until the job does NOT have the specified status with some timeout

    the default timeout of 25 if chosen because the task manager runs on a 20 second
    schedule, and the API does not guarentee working jobs faster than this
    """
    start = time.time()
    while time.time() - start < timeout:
        job.refresh_from_db()
        if job.status != status:
            return
    raise RuntimeError(f'Job failed to exit {status} in {timeout} seconds. job_explanation={job.job_explanation} tb={job.result_traceback}')


def test_launch_demo_jt(post, admin_user):
    jt = JobTemplate.objects.get(name='Demo Job Template')

    url = reverse('api:job_template_launch', kwargs={'pk': jt.id})

    r = post(url=url, data={}, user=admin_user, expect=201)
    job = Job.objects.get(pk=r.data['id'])

    wait_to_leave_status(job, 'pending')
    wait_to_leave_status(job, 'waiting')
    wait_to_leave_status(job, 'running', timeout=800)

    assert job.status == 'successful', f'Job was not successful id={job.id} status={job.status}'
