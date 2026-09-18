import pytest
from django.utils.timezone import now

from awx.main.management.commands.update_host_metric_inventory_counts import Command
from awx.main.models import Inventory, Host, Organization
from awx.main.models.inventory import HostMetric


@pytest.fixture
def org(db):
    return Organization.objects.create(name='test-org')


@pytest.fixture
def inventories(org):
    return [
        Inventory.objects.create(name='inv-1', organization=org),
        Inventory.objects.create(name='inv-2', organization=org),
        Inventory.objects.create(name='inv-3', organization=org),
    ]


@pytest.mark.django_db
def test_no_hosts_sets_zero(inventories):
    """HostMetric records with no matching Host rows get used_in_inventories=0."""
    current_time = now()
    HostMetric.objects.create(hostname='orphan-host', last_automation=current_time)

    Command().handle()

    hm = HostMetric.objects.get(hostname='orphan-host')
    assert hm.used_in_inventories == 0


@pytest.mark.django_db
def test_single_inventory(inventories):
    """Host in one inventory produces used_in_inventories=1."""
    current_time = now()
    Host.objects.create(name='host-a', inventory=inventories[0])
    HostMetric.objects.create(hostname='host-a', last_automation=current_time)

    Command().handle()

    hm = HostMetric.objects.get(hostname='host-a')
    assert hm.used_in_inventories == 1


@pytest.mark.django_db
def test_multiple_inventories(inventories):
    """Same hostname across 3 inventories produces used_in_inventories=3."""
    current_time = now()
    for inv in inventories:
        Host.objects.create(name='shared-host', inventory=inv)
    HostMetric.objects.create(hostname='shared-host', last_automation=current_time)

    Command().handle()

    hm = HostMetric.objects.get(hostname='shared-host')
    assert hm.used_in_inventories == 3


@pytest.mark.django_db
def test_mixed_hosts(inventories):
    """Different hosts with different inventory membership counts."""
    current_time = now()

    Host.objects.create(name='host-x', inventory=inventories[0])
    Host.objects.create(name='host-x', inventory=inventories[1])
    Host.objects.create(name='host-y', inventory=inventories[0])

    HostMetric.objects.create(hostname='host-x', last_automation=current_time)
    HostMetric.objects.create(hostname='host-y', last_automation=current_time)
    HostMetric.objects.create(hostname='host-z', last_automation=current_time)

    Command().handle()

    assert HostMetric.objects.get(hostname='host-x').used_in_inventories == 2
    assert HostMetric.objects.get(hostname='host-y').used_in_inventories == 1
    assert HostMetric.objects.get(hostname='host-z').used_in_inventories == 0


@pytest.mark.django_db
def test_idempotent(inventories):
    """Running the command twice produces the same result."""
    current_time = now()
    Host.objects.create(name='host-idem', inventory=inventories[0])
    Host.objects.create(name='host-idem', inventory=inventories[1])
    HostMetric.objects.create(hostname='host-idem', last_automation=current_time)

    Command().handle()
    assert HostMetric.objects.get(hostname='host-idem').used_in_inventories == 2

    Command().handle()
    assert HostMetric.objects.get(hostname='host-idem').used_in_inventories == 2


@pytest.mark.django_db
def test_updates_after_inventory_change(inventories):
    """Counts update correctly when a host is added to a new inventory."""
    current_time = now()
    Host.objects.create(name='host-grow', inventory=inventories[0])
    HostMetric.objects.create(hostname='host-grow', last_automation=current_time)

    Command().handle()
    assert HostMetric.objects.get(hostname='host-grow').used_in_inventories == 1

    Host.objects.create(name='host-grow', inventory=inventories[2])
    Command().handle()
    assert HostMetric.objects.get(hostname='host-grow').used_in_inventories == 2
