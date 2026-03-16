import logging

from django.utils.timezone import now

from awx.api.versioning import reverse
from awx.main.models import Inventory, Host, Job, JobTemplate

from awx.main.tests.live.tests.conftest import wait_for_job

logger = logging.getLogger(__name__)

NUM_HOSTS = 50
NUM_JOBS = 10


def test_run_jobs_against_many_hosts(live_tmp_folder, default_org, project_factory, post, admin):
    """Create an inventory with 50 hosts, then run several jobs against it."""

    # --- Inventory with 50 hosts ---
    inv_name = 'perf-test-inventory'
    Inventory.objects.filter(name=inv_name, organization=default_org).delete()
    inv = Inventory.objects.create(name=inv_name, organization=default_org)

    right_now = now()
    hosts = [Host(inventory=inv, name=f'host-{i}', created=right_now, modified=right_now) for i in range(NUM_HOSTS)]
    Host.objects.bulk_create(hosts)
    assert inv.hosts.count() == NUM_HOSTS
    logger.info(f'Created inventory {inv_name} with {NUM_HOSTS} hosts')

    # --- Project from local git repo ---
    proj = project_factory(scm_url=f'file://{live_tmp_folder}/debug')
    if proj.current_job:
        wait_for_job(proj.current_job)

    # --- Job Template ---
    jt_name = 'perf-test-jt'
    JobTemplate.objects.filter(name=jt_name).delete()
    result = post(
        reverse('api:job_template_list'),
        {'name': jt_name, 'project': proj.id, 'playbook': 'debug.yml', 'inventory': inv.id},
        admin,
        expect=201,
    )
    jt = JobTemplate.objects.get(id=result.data['id'])

    # --- Launch several jobs sequentially ---
    jobs = []
    for i in range(NUM_JOBS):
        job = jt.create_unified_job()
        job.signal_start()
        logger.info(f'Launched job {i+1}/{NUM_JOBS} id={job.id}')
        wait_for_job(job)
        jobs.append(job)

    # --- Verify all jobs succeeded and touched the right number of hosts ---
    for i, job in enumerate(jobs):
        job.refresh_from_db()
        assert job.status == 'successful', f'Job {i+1} id={job.id} status={job.status}'

        host_status = job.host_status_counts
        if host_status:
            total_hosts = sum(host_status.values())
            assert total_hosts == NUM_HOSTS, f'Job {i+1} ran against {total_hosts} hosts, expected {NUM_HOSTS}'
