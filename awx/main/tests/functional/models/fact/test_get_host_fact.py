import pytest

from datetime import timedelta
from django.utils import timezone

from awx.main.models import Fact


@pytest.mark.django_db
def test_newest_scan_exact(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    hosts = hosts(host_count=2)
    facts = fact_scans(fact_scans=3, timestamp_epoch=epoch)

    fact_known = None
    for f in facts:
        if f.host_id == hosts[0].id and f.module == 'ansible' and f.timestamp == epoch:
            fact_known = f
            break
    fact_found = Fact.get_host_fact(hosts[0].id, 'ansible', epoch)

    assert fact_found == fact_known


@pytest.mark.django_db
def test_newest_scan_less_than(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    '''
    Show me the most recent state of the sytem at any point of time.
    or, said differently
    For any timestamp, get the first scan that is <= the timestamp.
    '''

    '''
    Ensure most recent scan run is the scan returned.
    Query by future date.
    '''
    epoch = timezone.now()
    timestamp_future = epoch + timedelta(days=10)
    hosts = hosts(host_count=2)
    facts = fact_scans(fact_scans=3, timestamp_epoch=epoch)

    fact_known = None
    for f in facts:
        if f.host_id == hosts[0].id and f.module == 'ansible' and f.timestamp == epoch + timedelta(days=2):
            fact_known = f
            break
    assert fact_known is not None

    fact_found = Fact.get_host_fact(hosts[0].id, 'ansible', timestamp_future)

    assert fact_found == fact_known


@pytest.mark.django_db
def test_query_middle_of_timeline(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    '''
    Tests query Fact that is in the middle of the fact scan timeline, but not an exact timestamp.
    '''
    epoch = timezone.now()
    timestamp_middle = epoch + timedelta(days=1, hours=3)
    hosts = hosts(host_count=2)
    facts = fact_scans(fact_scans=3, timestamp_epoch=epoch)

    fact_known = None
    for f in facts:
        if f.host_id == hosts[0].id and f.module == 'ansible' and f.timestamp == epoch + timedelta(days=1):
            fact_known = f
            break
    assert fact_known is not None

    fact_found = Fact.get_host_fact(hosts[0].id, 'ansible', timestamp_middle)

    assert fact_found == fact_known


@pytest.mark.django_db
def test_query_result_empty(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    '''
    Query time less than any fact scan. Should return None
    '''
    epoch = timezone.now()
    timestamp_less = epoch - timedelta(days=1)
    hosts = hosts(host_count=2)
    fact_scans(fact_scans=3, timestamp_epoch=epoch)

    fact_found = Fact.get_host_fact(hosts[0].id, 'ansible', timestamp_less)

    assert fact_found is None


@pytest.mark.django_db
def test_by_module(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    '''
    Query by fact module other than 'ansible'
    '''
    epoch = timezone.now()
    hosts = hosts(host_count=2)
    facts = fact_scans(fact_scans=3, timestamp_epoch=epoch)

    fact_known_services = None
    fact_known_packages = None
    for f in facts:
        if f.host_id == hosts[0].id:
            if f.module == 'services' and f.timestamp == epoch:
                fact_known_services = f
            elif f.module == 'packages' and f.timestamp == epoch:
                fact_known_packages = f
    assert fact_known_services is not None
    assert fact_known_packages is not None

    fact_found_services = Fact.get_host_fact(hosts[0].id, 'services', epoch)
    fact_found_packages = Fact.get_host_fact(hosts[0].id, 'packages', epoch)

    assert fact_found_services == fact_known_services
    assert fact_found_packages == fact_known_packages
