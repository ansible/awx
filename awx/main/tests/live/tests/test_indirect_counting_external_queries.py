"""
Integration tests for external query file functionality (AAP-58470).

Tests verify the end-to-end external query file workflow for indirect node
counting using real AWX job execution. A fixture-created vendor collection
at /var/lib/awx/vendor_collections/ provides external query files, simulating
what the build-time (AAP-58426) and deployment (AAP-58557) integrations will
provide once available.

Test data:
- Collection 'demo.external' at various versions (no embedded query)
- External query files in mock redhat.indirect_accounting collection
"""

import os
import shutil
import time
import yaml

import pytest
from flags.state import enable_flag, disable_flag, flag_enabled

from awx.main.tests.live.tests.conftest import wait_for_events, unified_job_stdout
from awx.main.tasks.host_indirect import save_indirect_host_entries
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit
from awx.main.models.event_query import EventQuery
from awx.main.models import Job

# --- Constants ---

EXTERNAL_QUERY_JQ = '{name: .name, canonical_facts: {host_name: .direct_host_name}, facts: {device_type: .device_type}}'

EXTERNAL_QUERY_CONTENT = yaml.dump(
    {'demo.external.example': {'query': EXTERNAL_QUERY_JQ}},
    default_flow_style=False,
)

# For precedence test: different jq (no device_type in facts) so we can detect which query was used
EXTERNAL_QUERY_FOR_DEMO_QUERY_JQ = '{name: .name, canonical_facts: {host_name: .direct_host_name}, facts: {}}'

EXTERNAL_QUERY_FOR_DEMO_QUERY_CONTENT = yaml.dump(
    {'demo.query.example': {'query': EXTERNAL_QUERY_FOR_DEMO_QUERY_JQ}},
    default_flow_style=False,
)

VENDOR_COLLECTIONS_BASE = '/var/lib/awx/vendor_collections'


# --- Fixtures ---


@pytest.fixture
def enable_indirect_host_counting():
    """Enable FEATURE_INDIRECT_NODE_COUNTING_ENABLED flag for the test.

    Only creates a FlagState DB record if the flag isn't already enabled
    (e.g. via development_defaults.py), to avoid UniqueViolation errors
    and to avoid leaking state to other tests.
    """
    flag_name = "FEATURE_INDIRECT_NODE_COUNTING_ENABLED"
    was_enabled = flag_enabled(flag_name)
    if not was_enabled:
        enable_flag(flag_name)
    yield
    if not was_enabled:
        disable_flag(flag_name)


@pytest.fixture
def vendor_collections_dir():
    """Set up mock redhat.indirect_accounting collection at /var/lib/awx/vendor_collections/.

    Creates the collection structure with external query files:
    - demo.external.1.0.0.yml  (exact match for v1.0.0)
    - demo.external.1.1.0.yml  (fallback target for v1.5.0)
    - demo.query.0.0.1.yml     (for precedence test with embedded-query collection)
    """
    base = os.path.join(VENDOR_COLLECTIONS_BASE, 'ansible_collections', 'redhat', 'indirect_accounting')
    queries_path = os.path.join(base, 'extensions', 'audit', 'external_queries')
    meta_path = os.path.join(base, 'meta')

    os.makedirs(queries_path, exist_ok=True)
    os.makedirs(meta_path, exist_ok=True)

    # galaxy.yml for valid collection structure
    with open(os.path.join(base, 'galaxy.yml'), 'w') as f:
        yaml.dump(
            {
                'namespace': 'redhat',
                'name': 'indirect_accounting',
                'version': '1.0.0',
                'description': 'Test fixture for external query integration tests',
                'authors': ['AWX Tests'],
                'dependencies': {},
            },
            f,
        )

    # meta/runtime.yml
    with open(os.path.join(meta_path, 'runtime.yml'), 'w') as f:
        yaml.dump({'requires_ansible': '>=2.15.0'}, f)

    # External query files for demo.external collection
    for version in ('1.0.0', '1.1.0'):
        with open(os.path.join(queries_path, f'demo.external.{version}.yml'), 'w') as f:
            f.write(EXTERNAL_QUERY_CONTENT)

    # External query file for demo.query collection (precedence test)
    with open(os.path.join(queries_path, 'demo.query.0.0.1.yml'), 'w') as f:
        f.write(EXTERNAL_QUERY_FOR_DEMO_QUERY_CONTENT)

    yield base

    # Cleanup
    shutil.rmtree(VENDOR_COLLECTIONS_BASE, ignore_errors=True)


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up EventQuery and IndirectManagedNodeAudit records after each test."""
    yield
    EventQuery.objects.filter(fqcn='demo.external').delete()
    EventQuery.objects.filter(fqcn='demo.query').delete()
    IndirectManagedNodeAudit.objects.filter(job__name__icontains='external_query').delete()


# --- Helpers ---


def run_external_query_job(run_job_from_playbook, live_tmp_folder, test_name, project_dir, jt_params=None):
    """Run a job and return the Job object after waiting for indirect host processing."""
    scm_url = f'file://{live_tmp_folder}/{project_dir}'
    run_job_from_playbook(test_name, 'run_task.yml', scm_url=scm_url, jt_params=jt_params)

    job = Job.objects.filter(name__icontains=test_name).order_by('-created').first()
    assert job is not None, f'Job not found for test {test_name}'
    wait_for_events(job)

    return job


def wait_for_indirect_processing(job, expect_records=True, timeout=5):
    """Wait for indirect host processing to complete.

    Follows the same pattern as test_indirect_host_counting.py:53-72.
    """
    # Ensure indirect host processing runs (wait_for_events already called by caller)
    job.refresh_from_db()
    if job.event_queries_processed is False:
        save_indirect_host_entries.delay(job.id, wait_for_events=False)

    if expect_records:
        # Poll for audit records to appear
        for _ in range(20):
            if IndirectManagedNodeAudit.objects.filter(job=job).exists():
                break
            time.sleep(0.25)
        else:
            raise RuntimeError(f'No IndirectManagedNodeAudit records populated for job_id={job.id}')
    else:
        # For negative tests, wait a reasonable time to confirm no records appear
        time.sleep(timeout)
        job.refresh_from_db()


# --- AC8.1: External query populates IndirectManagedNodeAudit correctly ---


def test_external_query_populates_audit_table(live_tmp_folder, run_job_from_playbook, enable_indirect_host_counting, vendor_collections_dir):
    """AC8.1: Job using demo.external.example with external query file populates
    IndirectManagedNodeAudit table correctly.

    Uses demo.external v1.0.0 with exact-match external query file demo.external.1.0.0.yml.
    """
    job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_1',
        'test_host_query_external_v1_0_0',
    )
    wait_for_indirect_processing(job, expect_records=True)

    # Verify installed_collections captured demo.external
    assert 'demo.external' in job.installed_collections
    assert 'host_query' in job.installed_collections['demo.external']

    # Verify IndirectManagedNodeAudit records
    assert IndirectManagedNodeAudit.objects.filter(job=job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=job).first()

    assert host_audit.canonical_facts == {'host_name': 'foo_host_default'}
    assert host_audit.facts == {'device_type': 'Fake Host'}
    assert host_audit.name == 'vm-foo'
    assert host_audit.organization == job.organization
    assert 'demo.external.example' in host_audit.events


# --- AC8.2: Precedence - embedded query takes precedence over external ---


def test_embedded_query_takes_precedence(live_tmp_folder, run_job_from_playbook, enable_indirect_host_counting, vendor_collections_dir):
    """AC8.2: When collection has both embedded and external query files,
    the embedded query takes precedence.

    Uses demo.query v0.0.1 which HAS an embedded query (extensions/audit/event_query.yml).
    An external query (demo.query.0.0.1.yml) also exists but uses a different jq expression
    (no device_type in facts). By checking the audit record's facts, we verify which query was used.
    """
    # Run with demo.query collection (has embedded query)
    job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_2',
        'test_host_query',
    )
    wait_for_indirect_processing(job, expect_records=True)

    # Verify the embedded query was used (includes device_type in facts)
    host_audit = IndirectManagedNodeAudit.objects.filter(job=job).first()
    assert host_audit.facts == {'device_type': 'Fake Host'}, (
        'Expected embedded query output (with device_type). ' 'If facts is {}, the external query was incorrectly used instead.'
    )


# --- AC8.3: Version fallback to compatible version ---


def test_fallback_to_compatible_version(live_tmp_folder, run_job_from_playbook, enable_indirect_host_counting, vendor_collections_dir):
    """AC8.3: Job using collection version with no exact query file falls back
    correctly to compatible version.

    Uses demo.external v1.5.0. No demo.external.1.5.0.yml exists, but
    demo.external.1.1.0.yml is available (same major version, highest <= 1.5.0).
    The fallback should find and use the 1.1.0 query.
    """
    job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_3',
        'test_host_query_external_v1_5_0',
    )
    wait_for_indirect_processing(job, expect_records=True)

    # Verify installed_collections captured demo.external at v1.5.0
    assert 'demo.external' in job.installed_collections
    assert job.installed_collections['demo.external']['version'] == '1.5.0'

    # Verify IndirectManagedNodeAudit records were created via fallback
    assert IndirectManagedNodeAudit.objects.filter(job=job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=job).first()

    assert host_audit.canonical_facts == {'host_name': 'foo_host_default'}
    assert host_audit.facts == {'device_type': 'Fake Host'}
    assert host_audit.name == 'vm-foo'


# --- AC8.4: Fallback queries don't overcount ---


def test_fallback_does_not_overcount(live_tmp_folder, run_job_from_playbook, enable_indirect_host_counting, vendor_collections_dir):
    """AC8.4: Fallback queries don't count MORE nodes than exact-version queries.

    Runs two jobs:
    1. Exact match scenario (demo.external v1.0.0 -> demo.external.1.0.0.yml)
    2. Fallback scenario (demo.external v1.5.0 -> falls back to demo.external.1.1.0.yml)

    Verifies that fallback record count <= exact record count.
    """
    # Run exact-match job
    exact_job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_4_exact',
        'test_host_query_external_v1_0_0',
    )
    wait_for_indirect_processing(exact_job, expect_records=True)
    exact_count = IndirectManagedNodeAudit.objects.filter(job=exact_job).count()

    # Run fallback job
    fallback_job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_4_fallback',
        'test_host_query_external_v1_5_0',
    )
    wait_for_indirect_processing(fallback_job, expect_records=True)
    fallback_count = IndirectManagedNodeAudit.objects.filter(job=fallback_job).count()

    # Critical safety check: fallback must never count MORE than exact
    assert fallback_count <= exact_count, (
        f'Overcounting detected! Fallback produced {fallback_count} records ' f'but exact match produced only {exact_count} records.'
    )

    # Both use the same jq expression and same module, so counts should be equal
    assert exact_count == fallback_count


# --- AC8.5: Warning logs contain correct version information ---


def test_fallback_log_contains_version_info(live_tmp_folder, run_job_from_playbook, enable_indirect_host_counting, vendor_collections_dir):
    """AC8.5: Warning logs contain correct version information when fallback is used.

    Runs a job with verbosity=1 so callback plugin verbose output is captured.
    Verifies the log contains the installed version (1.5.0), fallback version (1.1.0),
    and collection FQCN (demo.external).
    """
    job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_5',
        'test_host_query_external_v1_5_0',
        jt_params={'verbosity': 1},
    )
    wait_for_indirect_processing(job, expect_records=True)

    # Get job stdout to check for fallback log message
    stdout = unified_job_stdout(job)

    # The callback plugin emits: "Using external query {version_used} for {fqcn} v{ver}."
    assert '1.1.0' in stdout, f'Fallback version 1.1.0 not found in job stdout. stdout:\n{stdout}'
    assert 'demo.external' in stdout, f'Collection FQCN demo.external not found in job stdout. stdout:\n{stdout}'
    assert '1.5.0' in stdout, f'Installed version 1.5.0 not found in job stdout. stdout:\n{stdout}'


# --- AC8.6: No counting when no compatible fallback exists ---


def test_no_counting_without_compatible_fallback(live_tmp_folder, run_job_from_playbook, enable_indirect_host_counting, vendor_collections_dir):
    """AC8.6: No counting occurs when no compatible fallback exists.

    Uses demo.external v3.0.0 with only v1.x external query files available.
    Since major versions differ (3 vs 1), no fallback should occur and no
    IndirectManagedNodeAudit records should be created.
    """
    job = run_external_query_job(
        run_job_from_playbook,
        live_tmp_folder,
        'external_query_ac8_6',
        'test_host_query_external_v3_0_0',
    )
    wait_for_indirect_processing(job, expect_records=False)

    # No audit records should exist for this job
    assert IndirectManagedNodeAudit.objects.filter(job=job).count() == 0, (
        'IndirectManagedNodeAudit records were created despite no compatible ' 'fallback existing for demo.external v3.0.0 (only v1.x queries available).'
    )
