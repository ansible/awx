import time

from awx.api.versioning import reverse

from awx.main.models import JobTemplate, Job


def test_launch_demo_jt(post, admin_user):
    jt = JobTemplate.objects.get(name='Demo Job Template')

    url = reverse('api:job_template_launch', kwargs={'pk': jt.id})

    r = post(url=url, data={}, user=admin_user, expect=201)
    job = Job.objects.get(pk=r.data['id'])

    # Loop to wait for task manager processing
    start = time.time()
    while time.time() - start < 25:
        job.refresh_from_db()
        if job.status != 'pending':
            break

    # Loop to wait for dispatcher
    start = time.time()
    while time.time() - start < 25:
        job.refresh_from_db()
        if job.status != 'waiting':
            break

    # Loop to wait for job to actually finish
    start = time.time()
    while time.time() - start < 800:
        job.refresh_from_db()
        if job.status != 'running':
            break

    assert job.status == 'successful', f'Job was not successful id={job.id} status={job.status}'
