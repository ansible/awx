from awx.api.versioning import reverse

from awx.main.models import JobTemplate, Job

from awx.main.tests.live.tests.conftest import wait_for_job


def test_launch_demo_jt(post, admin):
    jt = JobTemplate.objects.get(name='Demo Job Template')

    url = reverse('api:job_template_launch', kwargs={'pk': jt.id})

    r = post(url=url, data={}, user=admin, expect=201)
    job = Job.objects.get(pk=r.data['id'])
    wait_for_job(job)
