import pytest

from datetime import timedelta

from django.utils import timezone

from awx.main.models import Fact


def setup_common(hosts, fact_scans, ts_from=None, ts_to=None, epoch=timezone.now(), module_name='ansible', ts_known=None):
    hosts = hosts(host_count=2)
    facts = fact_scans(fact_scans=3, timestamp_epoch=epoch)

    facts_known = []
    for f in facts:
        if f.host.id == hosts[0].id:
            if module_name and f.module != module_name:
                continue
            if ts_known and f.timestamp != ts_known:
                continue
            facts_known.append(f)
    fact_objs = Fact.get_timeline(hosts[0].id, module=module_name, ts_from=ts_from, ts_to=ts_to)
    return (facts_known, fact_objs)


@pytest.mark.django_db
def test_all(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_from = epoch - timedelta(days=1)
    ts_to = epoch + timedelta(days=10)

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from, ts_to, module_name=None, epoch=epoch)
    assert 9 == len(facts_known)
    assert 9 == len(fact_objs)


@pytest.mark.django_db
def test_all_ansible(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_from = epoch - timedelta(days=1)
    ts_to = epoch + timedelta(days=10)

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from, ts_to, epoch=epoch)
    assert 3 == len(facts_known)
    assert 3 == len(fact_objs)

    for i in range(len(facts_known) - 1, 0):
        assert facts_known[i].id == fact_objs[i].id


@pytest.mark.django_db
def test_empty_db(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    hosts = hosts(host_count=2)
    epoch = timezone.now()
    ts_from = epoch - timedelta(days=1)
    ts_to = epoch + timedelta(days=10)

    fact_objs = Fact.get_timeline(hosts[0].id, 'ansible', ts_from, ts_to)

    assert 0 == len(fact_objs)


@pytest.mark.django_db
def test_no_results(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_from = epoch - timedelta(days=100)
    ts_to = epoch - timedelta(days=50)

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from, ts_to, epoch=epoch)
    assert 0 == len(fact_objs)


@pytest.mark.django_db
def test_exact_same_equal(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_to = ts_from = epoch + timedelta(days=1)

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from, ts_to, ts_known=ts_to, epoch=epoch)
    assert 1 == len(facts_known)
    assert 1 == len(fact_objs)

    assert facts_known[0].id == fact_objs[0].id


@pytest.mark.django_db
def test_exact_from_exclusive_to_inclusive(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_from = epoch + timedelta(days=1)
    ts_to = epoch + timedelta(days=2)

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from, ts_to, ts_known=ts_to, epoch=epoch)

    assert 1 == len(facts_known)
    assert 1 == len(fact_objs)

    assert facts_known[0].id == fact_objs[0].id


@pytest.mark.django_db
def test_to_lte(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_to = epoch + timedelta(days=1)

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from=None, ts_to=ts_to, epoch=epoch)
    facts_known_subset = list(filter(lambda x: x.timestamp <= ts_to, facts_known))

    assert 2 == len(facts_known_subset)
    assert 2 == len(fact_objs)

    for i in range(0, len(fact_objs)):
        assert facts_known_subset[len(facts_known_subset) - i - 1].id == fact_objs[i].id


@pytest.mark.django_db
def test_from_gt(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    ts_from = epoch

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from=ts_from, ts_to=None, epoch=epoch)
    facts_known_subset = list(filter(lambda x: x.timestamp > ts_from, facts_known))

    assert 2 == len(facts_known_subset)
    assert 2 == len(fact_objs)

    for i in range(0, len(fact_objs)):
        assert facts_known_subset[len(facts_known_subset) - i - 1].id == fact_objs[i].id


@pytest.mark.django_db
def test_no_ts(hosts, fact_scans, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()

    (facts_known, fact_objs) = setup_common(hosts, fact_scans, ts_from=None, ts_to=None, epoch=epoch)
    assert 3 == len(facts_known)
    assert 3 == len(fact_objs)

    for i in range(len(facts_known) - 1, 0):
        assert facts_known[i].id == fact_objs[i].id
