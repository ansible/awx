"""
Unit tests for timezone-related fact gathering bugs.

These tests reveal the bug in finish_fact_cache() where file modification time
comparisons fail when the controller is in UTC but managed nodes are in other
timezones (CEST, PST, JST), causing facts to not be stored correctly.
"""

import pytest
import os
import json
import codecs
from datetime import timedelta
from unittest import mock

from awx.main.models import Host, Inventory
from awx.main.tasks.facts import start_fact_cache, finish_fact_cache
from django.utils.timezone import now


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings.ANSIBLE_FACT_CACHE_TIMEOUT for all tests"""
    with mock.patch('awx.main.tasks.facts.settings') as mock_settings_obj:
        mock_settings_obj.ANSIBLE_FACT_CACHE_TIMEOUT = 86400  # 24 hours default
        yield mock_settings_obj


@pytest.fixture
def inventory():
    """Create a mock inventory (not saved to database)"""
    return Inventory(id=42, name='Test Inventory')


@pytest.fixture
def hosts_multi_timezone(inventory):
    """
    Create mock hosts simulating different timezones.
    These are not saved to the database - just mock objects for testing.
    """
    ref_time = now()

    # Host 1: UTC timezone (controller timezone)
    utc_host = Host(id=1, name='utc-host', inventory=inventory, ansible_facts={'timezone': 'UTC', 'test_fact': 'utc_value'}, ansible_facts_modified=ref_time)

    # Host 2: CEST timezone (UTC+2)
    cest_host = Host(
        id=2, name='cest-host', inventory=inventory, ansible_facts={'timezone': 'CEST', 'test_fact': 'cest_value'}, ansible_facts_modified=ref_time
    )

    # Host 3: PST timezone (UTC-8)
    pst_host = Host(id=3, name='pst-host', inventory=inventory, ansible_facts={'timezone': 'PST', 'test_fact': 'pst_value'}, ansible_facts_modified=ref_time)

    return [utc_host, cest_host, pst_host]


def test_fact_cache_timezone_file_mtime_comparison(inventory, hosts_multi_timezone, tmpdir, mocker):
    """
    Test that reveals the timezone bug in finish_fact_cache().

    The bug is in facts.py:111 where file modification times are compared.
    When a file is written on a host in CEST timezone but the controller
    is in UTC, the mtime comparison can fail because:

    1. start_fact_cache() writes facts and records the mtime
    2. During playbook execution, Ansible updates the fact file
    3. finish_fact_cache() compares the new mtime to the old one
    4. If timezones differ, the comparison may incorrectly determine
       that the file hasn't been modified
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Step 1: Start fact cache (simulates beginning of playbook run)
    start_fact_cache(hosts_multi_timezone, str(artifacts_dir), inventory_id=inventory.id)

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    # Step 2: Simulate Ansible updating facts on hosts
    # We'll update the fact files to simulate new facts being gathered
    for host in hosts_multi_timezone:
        filepath = os.path.join(fact_cache_dir, host.name)

        # Update the fact file with new data
        new_facts = host.ansible_facts.copy()
        new_facts['updated_fact'] = f'new_value_from_{host.ansible_facts["timezone"]}'

        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            os.chmod(f.name, 0o600)
            json.dump(new_facts, f)

    # Mock the database query that finish_fact_cache makes
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter(hosts_multi_timezone)
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)

    # Mock bulk_update to avoid database writes
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Step 3: Call finish_fact_cache to process updated facts
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # Step 4: Verify all hosts got their facts updated
    for host in hosts_multi_timezone:
        # This assertion should pass, but may fail due to timezone bug
        assert 'updated_fact' in host.ansible_facts, (
            f"Host {host.name} in {host.ansible_facts.get('timezone')} timezone "
            f"did not get facts updated. This reveals the timezone bug where "
            f"non-UTC hosts are filtered out during fact caching."
        )

        # Verify the specific updated value
        expected_value = f"new_value_from_{host.ansible_facts['timezone']}"
        actual_value = host.ansible_facts.get('updated_fact')

        assert actual_value == expected_value, (
            f"Host {host.name} expected fact value '{expected_value}' " f"but got '{actual_value}'. Timezone: {host.ansible_facts.get('timezone')}"
        )


def test_fact_cache_timezone_mtime_edge_case(inventory, hosts_multi_timezone, tmpdir, mocker):
    """
    Test that the fix correctly handles file mtime comparisons.

    This test verifies that using summary.get('last_write_time') as the baseline
    correctly identifies which files were modified after the playbook started,
    regardless of artificial mtime offsets.
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Start fact cache
    start_fact_cache(hosts_multi_timezone, str(artifacts_dir), inventory_id=inventory.id)

    # Get the baseline timestamp from inside the summary (this is what the fix uses)
    summary_path = os.path.join(artifacts_dir, 'host_cache_summary.json')
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    facts_write_time = summary.get('last_write_time')

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    # Simulate timezone offset scenarios
    for i, host in enumerate(hosts_multi_timezone):
        filepath = os.path.join(fact_cache_dir, host.name)

        # Update facts
        new_facts = host.ansible_facts.copy()
        new_facts['tz_test'] = f'updated_{host.name}'

        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            os.chmod(f.name, 0o600)
            json.dump(new_facts, f)

        # Simulate timezone offset by modifying the file's mtime
        # UTC host: no offset (i=0)
        # CEST host: +2 hours offset (i=1)
        # PST host: -8 hours offset (i=2)
        timezone_offsets = [0, 2 * 3600, -8 * 3600]  # in seconds

        # Set mtime to be AFTER facts_write_time but with timezone offset
        new_mtime = facts_write_time + 10 + timezone_offsets[i]
        os.utime(filepath, (new_mtime, new_mtime))

    # Mock the database query and bulk update
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter(hosts_multi_timezone)
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Finish fact cache - this is where the bug manifests
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # Check results
    utc_host, cest_host, pst_host = hosts_multi_timezone

    # UTC host: mtime = baseline + 10, should be updated
    assert 'tz_test' in utc_host.ansible_facts, "UTC host facts should be updated"

    # CEST host: mtime = baseline + 10 + 7200 (2h), should be updated
    assert 'tz_test' in cest_host.ansible_facts, "CEST host facts should be updated (mtime > baseline)"

    # PST host: mtime = baseline + 10 - 28800 (8h), should NOT be updated
    # This simulates a file that appears older than the baseline
    assert 'tz_test' not in pst_host.ansible_facts, (
        "PST host facts should NOT be updated because the artificial -8h offset " "makes the file appear older than the baseline timestamp"
    )


def test_fact_cache_same_mtime_different_timezone(inventory, tmpdir, mocker):
    """
    Test the specific scenario from AAP-54894:
    File modification time in local timezone vs database timestamp in UTC
    causes facts to appear stale when they're actually newer.
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Create a host with existing facts
    host = Host(
        id=99,
        name='tz-bug-host',
        inventory=inventory,
        ansible_facts={'last_update': '2025-07-29 06:31:54 CEST'},
        ansible_facts_modified=now() - timedelta(hours=1),  # 1 hour ago
    )

    # Start fact cache
    start_fact_cache([host], str(artifacts_dir), inventory_id=inventory.id)

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')
    filepath = os.path.join(fact_cache_dir, host.name)

    # Simulate Ansible updating the fact file with newer data
    # This represents the actual file on the managed node in CEST timezone
    new_facts = {'last_update': '2025-07-29 06:35:30 CEST', 'timezone': 'CEST'}  # 3m 36s later

    with codecs.open(filepath, 'w', encoding='utf-8') as f:
        os.chmod(f.name, 0o600)
        json.dump(new_facts, f)

    # Mock the database query and bulk update
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter([host])
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # The bug: even though the fact file has newer timestamp,
    # the mtime comparison might fail
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # This should pass but may fail due to timezone bug
    assert host.ansible_facts.get('last_update') == '2025-07-29 06:35:30 CEST', (
        f"Facts were not updated. Expected '2025-07-29 06:35:30 CEST' "
        f"but got '{host.ansible_facts.get('last_update')}'. "
        f"This is the AAP-54894 bug: timezone mismatch prevents fact updates."
    )

    # Verify facts were actually updated (not stale)
    assert host.ansible_facts_modified is not None
    assert host.ansible_facts_modified > now() - timedelta(minutes=1), "ansible_facts_modified should be recent, indicating facts were updated"


def test_fact_cache_clock_skew_between_controller_and_node(inventory, tmpdir, mocker):
    """
    Test scenario where controller clock and managed node clock are out of sync
    due to timezone differences, causing facts to be incorrectly filtered.
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Create hosts
    hosts = []
    for i, tz in enumerate(['UTC', 'CEST', 'JST', 'PST']):
        host = Host(
            id=100 + i, name=f'{tz.lower()}-host', inventory=inventory, ansible_facts={'timezone': tz, 'original': 'data'}, ansible_facts_modified=now()
        )
        hosts.append(host)

    # Start fact cache
    start_fact_cache(hosts, str(artifacts_dir), inventory_id=inventory.id)

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    # Simulate facts being updated on each host
    # Each host updates at "the same time" in their local timezone
    for host in hosts:
        filepath = os.path.join(fact_cache_dir, host.name)

        new_facts = {'timezone': host.ansible_facts['timezone'], 'updated': True}

        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            os.chmod(f.name, 0o600)
            json.dump(new_facts, f)

    # Mock the database query and bulk update
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter(hosts)
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Process facts
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # All hosts should have updated facts
    for host in hosts:
        assert host.ansible_facts.get('updated') is True, (
            f"Host {host.name} in {host.ansible_facts.get('timezone')} timezone " f"did not get updated facts. This reveals timezone filtering bug."
        )


def test_fact_cache_with_ansible_runner_modified_list(inventory, tmpdir, mocker):
    """
    Test that finish_fact_cache() correctly uses the fact_cache_modified.json file
    provided by ansible-runner to determine which facts were modified.

    This is the preferred solution that eliminates timezone issues by having
    ansible-runner detect modifications on the execution node using its local clock.
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Create test hosts
    hosts = [
        Host(id=1, name='localhost', inventory=inventory, ansible_facts={'old': 'data1'}, ansible_facts_modified=now()),
        Host(id=2, name='host2', inventory=inventory, ansible_facts={'old': 'data2'}, ansible_facts_modified=now()),
        Host(id=3, name='host3', inventory=inventory, ansible_facts={'old': 'data3'}, ansible_facts_modified=now()),
    ]

    # Start fact cache
    start_fact_cache(hosts, str(artifacts_dir), inventory_id=inventory.id)

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    # Update fact files for all hosts
    for host in hosts:
        filepath = os.path.join(fact_cache_dir, host.name)
        new_facts = {'new': f'updated_{host.name}'}

        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            os.chmod(f.name, 0o600)
            json.dump(new_facts, f)

    # Simulate ansible-runner writing the fact_cache_modified.json file
    # ansible-runner detected that only 'localhost' and 'host3' were modified
    modified_list = {'modified_files': ['localhost', 'host3']}  # host2 NOT in the list

    fact_cache_modified_file = os.path.join(artifacts_dir, 'fact_cache_modified.json')
    with open(fact_cache_modified_file, 'w', encoding='utf-8') as f:
        json.dump(modified_list, f, indent=2)

    # Mock the database query and bulk update
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter(hosts)
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Process facts
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # Verify: Only localhost and host3 should be updated (per ansible-runner's list)
    localhost, host2, host3 = hosts

    assert localhost.ansible_facts.get('new') == 'updated_localhost', "localhost should be updated (in modified_files list)"

    assert host2.ansible_facts.get('new') is None, "host2 should NOT be updated (not in modified_files list)"
    assert host2.ansible_facts.get('old') == 'data2', "host2 should retain old facts"

    assert host3.ansible_facts.get('new') == 'updated_host3', "host3 should be updated (in modified_files list)"


def test_fact_cache_fallback_to_timestamp_when_no_modified_list(inventory, tmpdir, mocker):
    """
    Test that finish_fact_cache() falls back to timestamp comparison
    when fact_cache_modified.json is not provided by ansible-runner.

    This ensures backward compatibility with older ansible-runner versions.
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Create test hosts
    hosts = [
        Host(id=1, name='testhost', inventory=inventory, ansible_facts={'version': 1}, ansible_facts_modified=now()),
    ]

    # Start fact cache
    start_fact_cache(hosts, str(artifacts_dir), inventory_id=inventory.id)

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')
    filepath = os.path.join(fact_cache_dir, 'testhost')

    # Update the fact file
    new_facts = {'version': 2}
    with codecs.open(filepath, 'w', encoding='utf-8') as f:
        os.chmod(f.name, 0o600)
        json.dump(new_facts, f)

    # NOTE: We do NOT create fact_cache_modified.json
    # This simulates an older ansible-runner that doesn't provide this file

    # Mock the database query and bulk update
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter(hosts)
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Process facts
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # Verify: Host should still be updated using fallback timestamp comparison
    assert hosts[0].ansible_facts.get('version') == 2, (
        "Host facts should be updated even without fact_cache_modified.json " "(fallback to timestamp comparison)"
    )


def test_fact_cache_with_timezone_offset_and_modified_list(inventory, tmpdir, mocker):
    """
    Test that the ansible-runner modified list solution works correctly
    even when files have timezone-affected timestamps that would fail
    the old timestamp comparison method.

    This demonstrates the key benefit: ansible-runner's list is timezone-independent.
    """
    artifacts_dir = tmpdir.mkdir("artifacts")

    # Create hosts simulating different timezones
    hosts = [
        Host(id=1, name='utc-host', inventory=inventory, ansible_facts={'tz': 'UTC'}, ansible_facts_modified=now()),
        Host(id=2, name='est-host', inventory=inventory, ansible_facts={'tz': 'EST'}, ansible_facts_modified=now()),
    ]

    # Start fact cache
    start_fact_cache(hosts, str(artifacts_dir), inventory_id=inventory.id)

    # Get baseline timestamp
    summary_path = os.path.join(artifacts_dir, 'host_cache_summary.json')
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    facts_write_time = summary.get('last_write_time')

    fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

    # Update fact files
    for host in hosts:
        filepath = os.path.join(fact_cache_dir, host.name)
        new_facts = {'tz': host.ansible_facts['tz'], 'updated': True}

        with codecs.open(filepath, 'w', encoding='utf-8') as f:
            os.chmod(f.name, 0o600)
            json.dump(new_facts, f)

    # Simulate timezone bug: EST host file has mtime that appears OLDER than baseline
    # (This would cause timestamp comparison to fail)
    utc_filepath = os.path.join(fact_cache_dir, 'utc-host')
    est_filepath = os.path.join(fact_cache_dir, 'est-host')

    # UTC host: mtime after baseline (would pass timestamp check)
    os.utime(utc_filepath, (facts_write_time + 10, facts_write_time + 10))

    # EST host: mtime BEFORE baseline due to 5-hour timezone offset
    # (This simulates the bug: file modified but appears older)
    os.utime(est_filepath, (facts_write_time - 18000, facts_write_time - 18000))  # -5 hours

    # ansible-runner provides modified list (correctly identified both hosts)
    modified_list = {'modified_files': ['utc-host', 'est-host']}  # Both hosts actually modified

    fact_cache_modified_file = os.path.join(artifacts_dir, 'fact_cache_modified.json')
    with open(fact_cache_modified_file, 'w', encoding='utf-8') as f:
        json.dump(modified_list, f, indent=2)

    # Mock the database query and bulk update
    mock_qs = mocker.MagicMock()
    mock_qs.order_by.return_value.iterator.return_value = iter(hosts)
    mocker.patch.object(Host.objects, 'filter', return_value=mock_qs)
    mocker.patch('awx.main.tasks.facts.bulk_update_sorted_by_id')

    # Process facts
    finish_fact_cache(str(artifacts_dir), job_id=1, inventory_id=inventory.id)

    # Verify: BOTH hosts should be updated because ansible-runner's list is timezone-independent
    utc_host, est_host = hosts

    assert utc_host.ansible_facts.get('updated') is True, "UTC host should be updated"

    assert est_host.ansible_facts.get('updated') is True, (
        "EST host should be updated even though its mtime appears older than baseline. "
        "The ansible-runner modified list correctly identifies it as modified, "
        "eliminating the timezone bug."
    )
