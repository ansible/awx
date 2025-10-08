import pytest
import os
import json
import tempfile
import codecs
from datetime import datetime, timedelta
from unittest import mock

from django.utils.timezone import now

from awx.main.models import Host, Inventory, Organization
from awx.main.tasks.facts import start_fact_cache, finish_fact_cache


# Mock settings for all tests in this module
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings.ANSIBLE_FACT_CACHE_TIMEOUT for all tests"""
    with mock.patch('awx.main.tasks.facts.settings') as mock_settings_obj:
        mock_settings_obj.ANSIBLE_FACT_CACHE_TIMEOUT = 86400  # 24 hours default
        yield mock_settings_obj


@pytest.mark.django_db
class TestHostFactsTimezone:
    """
    Tests to reveal timezone-related bugs in fact gathering.

    Bug scenario: When the Automation Controller is in UTC timezone but managed
    nodes are in other timezones (CEST, PST, JST), facts may not be stored correctly
    due to file modification time comparison issues in finish_fact_cache().
    """

    @pytest.fixture
    def organization(self):
        """Create a test organization"""
        org = Organization.objects.create(name='Test Org')
        return org

    @pytest.fixture
    def inventory(self, organization):
        """Create a test inventory"""
        inv = Inventory.objects.create(name='Test Inventory', organization=organization)
        return inv

    @pytest.fixture
    def hosts_multi_timezone(self, inventory):
        """
        Create hosts simulating different timezones.
        In reality, we can't change the actual timezone of the test environment,
        but we can simulate the behavior by manipulating timestamps.
        """
        # Host 1: UTC timezone (controller timezone)
        utc_host = Host.objects.create(
            name='utc-host', inventory=inventory, ansible_facts={'timezone': 'UTC', 'test_fact': 'utc_value'}, ansible_facts_modified=now()
        )

        # Host 2: CEST timezone (UTC+2)
        cest_host = Host.objects.create(
            name='cest-host', inventory=inventory, ansible_facts={'timezone': 'CEST', 'test_fact': 'cest_value'}, ansible_facts_modified=now()
        )

        # Host 3: PST timezone (UTC-8)
        pst_host = Host.objects.create(
            name='pst-host', inventory=inventory, ansible_facts={'timezone': 'PST', 'test_fact': 'pst_value'}, ansible_facts_modified=now()
        )

        return [utc_host, cest_host, pst_host]

    def test_fact_cache_timezone_file_mtime_comparison(self, inventory, hosts_multi_timezone):
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
        with tempfile.TemporaryDirectory() as artifacts_dir:
            # Step 1: Start fact cache (simulates beginning of playbook run)
            start_fact_cache(hosts_multi_timezone, artifacts_dir, inventory_id=inventory.id)

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

            # Step 3: Call finish_fact_cache to process updated facts
            finish_fact_cache(artifacts_dir, job_id=1, inventory_id=inventory.id)

            # Step 4: Verify all hosts got their facts updated
            for host in hosts_multi_timezone:
                host.refresh_from_db()

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

    def test_fact_cache_timezone_mtime_edge_case(self, inventory, hosts_multi_timezone):
        """
        Test edge case where file mtime is manipulated to simulate timezone offset.

        This test directly manipulates file modification times to simulate
        what happens when a file is created in a different timezone.
        """
        with tempfile.TemporaryDirectory() as artifacts_dir:
            # Start fact cache
            start_fact_cache(hosts_multi_timezone, artifacts_dir, inventory_id=inventory.id)

            # Read the summary file to get the facts_write_time
            summary_path = os.path.join(artifacts_dir, 'host_cache_summary.json')
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            # Get the mtime of summary file (this is what finish_fact_cache uses)
            facts_write_time = os.path.getmtime(summary_path)

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

            # Finish fact cache - this is where the bug manifests
            finish_fact_cache(artifacts_dir, job_id=1, inventory_id=inventory.id)

            # Check results
            utc_host, cest_host, pst_host = hosts_multi_timezone

            # Refresh from database
            utc_host.refresh_from_db()
            cest_host.refresh_from_db()
            pst_host.refresh_from_db()

            # UTC host should always work
            assert 'tz_test' in utc_host.ansible_facts, "UTC host facts should be updated"

            # BUG REVEAL: These assertions may fail due to timezone mtime comparison
            assert 'tz_test' in cest_host.ansible_facts, (
                f"CEST host facts were not updated. " f"File mtime comparison failed due to +2h timezone offset. " f"This reveals the bug in facts.py:111"
            )

            assert 'tz_test' in pst_host.ansible_facts, (
                f"PST host facts were not updated. " f"File mtime comparison failed due to -8h timezone offset. " f"This reveals the bug in facts.py:111"
            )

    def test_fact_cache_same_mtime_different_timezone(self, inventory):
        """
        Test the specific scenario from AAP-54894:
        File modification time in local timezone vs database timestamp in UTC
        causes facts to appear stale when they're actually newer.
        """
        with tempfile.TemporaryDirectory() as artifacts_dir:
            # Create a host with existing facts
            host = Host.objects.create(
                name='tz-bug-host',
                inventory=inventory,
                ansible_facts={'last_update': '2025-07-29 06:31:54 CEST'},
                ansible_facts_modified=now() - timedelta(hours=1),  # 1 hour ago
            )

            # Start fact cache
            start_fact_cache([host], artifacts_dir, inventory_id=inventory.id)

            fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')
            filepath = os.path.join(fact_cache_dir, host.name)

            # Simulate Ansible updating the fact file with newer data
            # This represents the actual file on the managed node in CEST timezone
            new_facts = {'last_update': '2025-07-29 06:35:30 CEST', 'timezone': 'CEST'}  # 3m 36s later

            with codecs.open(filepath, 'w', encoding='utf-8') as f:
                os.chmod(f.name, 0o600)
                json.dump(new_facts, f)

            # The bug: even though the fact file has newer timestamp,
            # the mtime comparison might fail
            finish_fact_cache(artifacts_dir, job_id=1, inventory_id=inventory.id)

            host.refresh_from_db()

            # This should pass but may fail due to timezone bug
            assert host.ansible_facts.get('last_update') == '2025-07-29 06:35:30 CEST', (
                f"Facts were not updated. Expected '2025-07-29 06:35:30 CEST' "
                f"but got '{host.ansible_facts.get('last_update')}'. "
                f"This is the AAP-54894 bug: timezone mismatch prevents fact updates."
            )

            # Verify facts were actually updated (not stale)
            assert host.ansible_facts_modified is not None
            assert host.ansible_facts_modified > now() - timedelta(minutes=1), "ansible_facts_modified should be recent, indicating facts were updated"

    @mock.patch('time.time')
    def test_fact_cache_clock_skew_between_controller_and_node(self, mock_time, inventory):
        """
        Test scenario where controller clock and managed node clock are out of sync
        due to timezone differences, causing facts to be incorrectly filtered.
        """
        with tempfile.TemporaryDirectory() as artifacts_dir:
            # Create hosts
            hosts = []
            for tz in ['UTC', 'CEST', 'JST', 'PST']:
                host = Host.objects.create(
                    name=f'{tz.lower()}-host', inventory=inventory, ansible_facts={'timezone': tz, 'original': 'data'}, ansible_facts_modified=now()
                )
                hosts.append(host)

            # Controller time (UTC)
            controller_time = 1722243114.0  # 2025-07-29 06:31:54 UTC
            mock_time.return_value = controller_time

            # Start fact cache
            start_fact_cache(hosts, artifacts_dir, inventory_id=inventory.id)

            fact_cache_dir = os.path.join(artifacts_dir, 'fact_cache')

            # Simulate facts being updated on each host
            # Each host updates at "the same time" in their local timezone
            for host in hosts:
                filepath = os.path.join(fact_cache_dir, host.name)

                new_facts = {'timezone': host.ansible_facts['timezone'], 'updated': True}

                with codecs.open(filepath, 'w', encoding='utf-8') as f:
                    os.chmod(f.name, 0o600)
                    json.dump(new_facts, f)

            # Process facts
            finish_fact_cache(artifacts_dir, job_id=1, inventory_id=inventory.id)

            # All hosts should have updated facts
            for host in hosts:
                host.refresh_from_db()
                assert host.ansible_facts.get('updated') is True, (
                    f"Host {host.name} in {host.ansible_facts.get('timezone')} timezone " f"did not get updated facts. This reveals timezone filtering bug."
                )
