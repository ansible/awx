import pytest
import datetime

from django.apps import apps
from django.conf import settings

from awx.main.models.inventory import Host
from awx.main.models.fact import Fact

from awx.main.migrations import _system_tracking as system_tracking

from awx.fact.models.fact import Fact as FactMongo
from awx.fact.models.fact import FactVersion, FactHost

def micro_to_milli(micro):
    return micro - (((int)(micro / 1000)) * 1000)

@pytest.mark.skipif(not getattr(settings, 'MONGO_DB', None), reason="MongoDB not configured")
@pytest.mark.django_db
@pytest.mark.mongo_db
def test_migrate_facts(inventories, hosts, hosts_mongo, fact_scans):
    inventory_objs = inventories(2)
    hosts(2, inventory_objs)
    hosts_mongo(2, inventory_objs)
    facts_known = fact_scans(2, inventory_objs)

    (migrated_count, not_migrated_count) = system_tracking.migrate_facts(apps, None)
    # 4 hosts w/ 2 fact scans each, 3 modules each scan
    assert migrated_count == 24
    assert not_migrated_count == 0


    for fact_mongo, fact_version in facts_known:
        host = Host.objects.get(inventory_id=fact_mongo.host.inventory_id, name=fact_mongo.host.hostname)
        t = fact_mongo.timestamp - datetime.timedelta(microseconds=micro_to_milli(fact_mongo.timestamp.microsecond))
        fact = Fact.objects.filter(host_id=host.id, timestamp=t, module=fact_mongo.module)

        assert len(fact) == 1
        assert fact[0] is not None

@pytest.mark.skipif(not getattr(settings, 'MONGO_DB', None), reason="MongoDB not configured")
@pytest.mark.django_db
@pytest.mark.mongo_db
def test_migrate_facts_hostname_does_not_exist(inventories, hosts, hosts_mongo, fact_scans):
    inventory_objs = inventories(2)
    host_objs = hosts(1, inventory_objs)
    hosts_mongo(2, inventory_objs)
    facts_known = fact_scans(2, inventory_objs)

    (migrated_count, not_migrated_count) = system_tracking.migrate_facts(apps, None)
    assert migrated_count == 12
    assert not_migrated_count == 12


    for fact_mongo, fact_version in facts_known:
        # Facts that don't match the only host will not be migrated
        if fact_mongo.host.hostname != host_objs[0].name:
            continue

        host = Host.objects.get(inventory_id=fact_mongo.host.inventory_id, name=fact_mongo.host.hostname)
        t = fact_mongo.timestamp - datetime.timedelta(microseconds=micro_to_milli(fact_mongo.timestamp.microsecond))
        fact = Fact.objects.filter(host_id=host.id, timestamp=t, module=fact_mongo.module)

        assert len(fact) == 1
        assert fact[0] is not None

@pytest.mark.skipif(not getattr(settings, 'MONGO_DB', None), reason="MongoDB not configured")
@pytest.mark.django_db
@pytest.mark.mongo_db
def test_drop_system_tracking_db(inventories, hosts, hosts_mongo, fact_scans):
    inventory_objs = inventories(1)
    hosts_mongo(1, inventory_objs)
    fact_scans(1, inventory_objs)

    assert FactMongo.objects.all().count() > 0
    assert FactVersion.objects.all().count() > 0
    assert FactHost.objects.all().count() > 0

    system_tracking.drop_system_tracking_db()

    assert FactMongo.objects.all().count() == 0
    assert FactVersion.objects.all().count() == 0
    assert FactHost.objects.all().count() == 0
