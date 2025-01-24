from awx.main.tasks.host_indirect import build_indirect_host_data
from awx.main.models import Job


def test_indirect_host_counting(live_tmp_folder, run_job_from_playbook):
    run_job_from_playbook('test_indirect_host_counting', 'run_task.yml', scm_url=f'file://{live_tmp_folder}/test_host_query')
    job = Job.objects.filter(name__icontains='test_indirect_host_counting').order_by('-created').first()

    # Data matches to awx/main/tests/data/projects/host_query/meta/event_query.yml
    # this just does things in-line to be a more localized test for the immediate testing
    event_query = {'demo.query.example': '{canonical_facts: {host_name: .direct_host_name}, facts: {device_type: .device_type}}'}

    # Run the task logic directly with local data
    results = build_indirect_host_data(job, event_query)
    assert len(results) == 1
    host_audit_entry = results[0]

    # Asserts on data that will match to the input jq string from above
    assert host_audit_entry.canonical_facts == {'host_name': 'foo_host_default'}
    assert host_audit_entry.facts == {'device_type': 'Fake Host'}
