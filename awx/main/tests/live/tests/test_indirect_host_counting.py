import yaml
import time

from awx.main.tests.live.tests.conftest import wait_for_events
from awx.main.tasks.host_indirect import build_indirect_host_data
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit
from awx.main.models import Job


def test_indirect_host_counting(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_indirect_host_counting', 'run_task.yml', scm_url=f'file://{live_tmp_folder}/test_host_query')
    job = Job.objects.filter(name__icontains='test_indirect_host_counting').order_by('-created').first()
    wait_for_events(job)  # We must wait for events because system tasks iterate on job.job_events.filter(...)

    # Data matches to awx/main/tests/data/projects/host_query/meta/event_query.yml
    # this just does things in-line to be a more localized test for the immediate testing
    module_jq_str = '{canonical_facts: {host_name: .direct_host_name}, facts: {device_type: .device_type}}'
    event_query = {'demo.query.example': module_jq_str}

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
    assert hq_data == {'demo.query.example': module_jq_str}

    assert job.ansible_version

    # This will poll, because it depends on the background task finishing
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
