"""
Tests for AAP-68023: host_list_rbac performance optimization.

The host list endpoint fetches the large ansible_facts JSON column
unnecessarily.  The HostManager now defers it by default so that
list queries avoid transferring this data from PostgreSQL.
"""

import pytest

from awx.main.models import Host

# ---------------------------------------------------------------------------
# AAP-68023: Verify ansible_facts column is deferred by HostManager
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHostManagerDeferral:
    """AAP-68023: The host list fetches 200+ columns unnecessarily.

    The ansible_facts JSON column is large and not used by the list
    serializer.  HostManager.get_queryset() must defer it so that
    every query through Host.objects avoids fetching it by default.
    """

    def test_ansible_facts_deferred_by_default(self):
        """ansible_facts should be in the deferred set for default Host queries."""
        qs = Host.objects.all()
        deferred = qs.query.deferred_loading[0]
        assert 'ansible_facts' in deferred, f'ansible_facts should be deferred by the HostManager. ' f'Deferred fields: {deferred}'

    def test_ansible_facts_accessible_when_needed(self, inventory):
        """Deferred fields are still accessible — Django fetches on access."""
        host = Host.objects.create(
            name='facts-host',
            inventory=inventory,
            ansible_facts={'os': 'linux'},
        )
        loaded = Host.objects.get(pk=host.pk)
        assert loaded.ansible_facts == {'os': 'linux'}
