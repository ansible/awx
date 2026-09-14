import yaml
import time

from django.core.management import call_command

from awx.main.tests.live.tests.conftest import wait_for_events
from awx.main.tasks.host_indirect import build_indirect_host_data, save_indirect_host_entries
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit
from awx.main.models import Job


def test_indirect_host_counting(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_indirect_host_counting', 'run_task.yml', scm_url=f'file://{live_tmp_folder}/test_host_query')
    job = Job.objects.filter(name__icontains='test_indirect_host_counting').order_by('-created').first()
    wait_for_events(job)  # We must wait for events because system tasks iterate on job.job_events.filter(...)

    # Data matches to awx/main/tests/data/projects/host_query/extensions/audit/event_query.yml
    # this just does things in-line to be a more localized test for the immediate testing
    module_jq_str = '{name: .name, canonical_facts: {host_name: .direct_host_name}, facts: {device_type: .device_type}}'
    event_query = {'demo.query.example': {'query': module_jq_str}}

    # Run the task logic directly with local data
    results = build_indirect_host_data(job, event_query)
    assert len(results) == 1
    host_audit_entry = results[0]

    canonical_facts = {'host_name': 'foo_host_default'}
    facts = {'device_type': 'Fake Host'}

    # Asserts on data that will match to the input jq string from above
    assert host_audit_entry.canonical_facts == canonical_facts
    assert host_audit_entry.facts == facts

    # Test collection of data
    assert 'demo.query' in job.installed_collections
    assert 'host_query' in job.installed_collections['demo.query']
    hq_text = job.installed_collections['demo.query']['host_query']
    hq_data = yaml.safe_load(hq_text)
    assert hq_data == {'demo.query.example': {'query': module_jq_str}}

    assert job.ansible_version

    # Poll for events finishing processing, because background task requires this
    for _ in range(10):
        if job.job_events.count() >= job.emitted_events:
            break
        time.sleep(0.2)
    else:
        raise RuntimeError(f'job id={job.id} never processed events')

    # Task might not run due to race condition, so make it run here
    job.refresh_from_db()
    if job.event_queries_processed is False:
        save_indirect_host_entries.delay(job.id, wait_for_events=False)

    # event_queries_processed only assures the task has started, it might take a minor amount of time to finish
    for _ in range(10):
        if IndirectManagedNodeAudit.objects.filter(job=job).exists():
            break
        time.sleep(0.2)
    else:
        raise RuntimeError(f'No IndirectManagedNodeAudit records ever populated for job_id={job.id}')

    assert IndirectManagedNodeAudit.objects.filter(job=job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=job).first()
    assert host_audit.canonical_facts == canonical_facts
    assert host_audit.facts == facts
    assert host_audit.organization == job.organization


def test_indirect_host_counting_runtime_toggle(live_tmp_folder, run_job_from_playbook):
    def run_job(test_name, project=None):
        result = run_job_from_playbook(
            test_name,
            'run_task.yml',
            scm_url=f'file://{live_tmp_folder}/test_host_query',
            proj=project,
        )
        job = result['job']
        wait_for_events(job)
        job.refresh_from_db()
        if job.event_queries_processed is False:
            save_indirect_host_entries.delay(job.id, wait_for_events=False)
        return job, result['project']

    def assert_audit_records(job, expected):
        if expected:
            for _ in range(25):
                if IndirectManagedNodeAudit.objects.filter(job=job).exists():
                    return
                time.sleep(0.2)
            assert IndirectManagedNodeAudit.objects.filter(job=job).exists()
        else:
            for _ in range(15):
                assert not IndirectManagedNodeAudit.objects.filter(job=job).exists()
                time.sleep(0.2)

    def wait_for_setting_propagation():
        # The dispatcher broadcasts setting cache invalidations to every worker.
        # Match the wait used by the live-test setting fixture before scheduling
        # a job that must observe the new value.
        time.sleep(5)

    call_command('set_indirect_node_counting', '--enable')
    wait_for_setting_propagation()
    try:
        enabled_job, project = run_job('indirect_counting_enabled')
        assert_audit_records(enabled_job, expected=True)

        call_command('set_indirect_node_counting', '--disable')
        wait_for_setting_propagation()
        disabled_job, project = run_job('indirect_counting_disabled', project)
        assert_audit_records(disabled_job, expected=False)

        call_command('set_indirect_node_counting', '--enable')
        wait_for_setting_propagation()
        reenabled_job, _ = run_job('indirect_counting_reenabled', project)
        assert_audit_records(reenabled_job, expected=True)
    finally:
        call_command('set_indirect_node_counting', '--enable')
