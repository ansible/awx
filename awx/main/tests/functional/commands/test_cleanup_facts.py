# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

# Python
import pytest
from unittest import mock
from dateutil.relativedelta import relativedelta
from datetime import timedelta

# Django
from django.utils import timezone
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands.cleanup_facts import CleanupFacts, Command
from awx.main.models.fact import Fact
from awx.main.models.inventory import Host


def mock_feature_enabled(feature):
    return True


def mock_feature_disabled(feature):
    return False


@pytest.mark.django_db
def test_cleanup_granularity(fact_scans, hosts, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    hosts(5)
    fact_scans(10, timestamp_epoch=epoch)
    fact_newest = Fact.objects.all().order_by('-timestamp').first()
    timestamp_future = fact_newest.timestamp + timedelta(days=365)
    granularity = relativedelta(days=2)

    cleanup_facts = CleanupFacts()
    deleted_count = cleanup_facts.cleanup(timestamp_future, granularity)
    assert 60 == deleted_count


@pytest.mark.django_db
def test_cleanup_older_than(fact_scans, hosts, monkeypatch_jsonbfield_get_db_prep_save):
    '''
    Delete half of the scans
    '''
    epoch = timezone.now()
    hosts(5)
    fact_scans(28, timestamp_epoch=epoch)
    qs = Fact.objects.all().order_by('-timestamp')
    fact_middle = qs[int(qs.count() / 2)]
    granularity = relativedelta()

    cleanup_facts = CleanupFacts()
    deleted_count = cleanup_facts.cleanup(fact_middle.timestamp, granularity)
    assert 210 == deleted_count


@pytest.mark.django_db
def test_cleanup_older_than_granularity_module(fact_scans, hosts, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    hosts(5)
    fact_scans(10, timestamp_epoch=epoch)
    fact_newest = Fact.objects.all().order_by('-timestamp').first()
    timestamp_future = fact_newest.timestamp + timedelta(days=365)
    granularity = relativedelta(days=2)

    cleanup_facts = CleanupFacts()
    deleted_count = cleanup_facts.cleanup(timestamp_future, granularity, module='ansible')
    assert 20 == deleted_count


@pytest.mark.django_db
def test_cleanup_logic(fact_scans, hosts, monkeypatch_jsonbfield_get_db_prep_save):
    '''
    Reduce the granularity of half of the facts scans, by half.
    '''
    epoch = timezone.now()
    hosts = hosts(5)
    fact_scans(60, timestamp_epoch=epoch)
    timestamp_middle = epoch + timedelta(days=30)
    granularity = relativedelta(days=2)
    module = 'ansible'

    cleanup_facts = CleanupFacts()
    cleanup_facts.cleanup(timestamp_middle, granularity, module=module)


    host_ids = Host.objects.all().values_list('id', flat=True)
    host_facts = {}
    for host_id in host_ids:
        facts = Fact.objects.filter(host__id=host_id, module=module, timestamp__lt=timestamp_middle).order_by('-timestamp')
        host_facts[host_id] = facts

    for host_id, facts in host_facts.items():
        assert 15 == len(facts)

        timestamp_pivot = timestamp_middle
        for fact in facts:
            timestamp_pivot -= granularity
            assert fact.timestamp == timestamp_pivot


@mock.patch('awx.main.management.commands.cleanup_facts.feature_enabled', new=mock_feature_disabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_system_tracking_feature_disabled(mocker):
    cmd = Command()
    with pytest.raises(CommandError) as err:
        cmd.handle(None)
    assert 'The System Tracking feature is not enabled for your instance' in str(err.value)


@mock.patch('awx.main.management.commands.cleanup_facts.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_parameters_ok(mocker):
    run = mocker.patch('awx.main.management.commands.cleanup_facts.CleanupFacts.run')
    kv = {
        'older_than': '1d',
        'granularity': '1d',
        'module': None,
    }
    cmd = Command()
    cmd.handle(None, **kv)
    run.assert_called_once_with(relativedelta(days=1), relativedelta(days=1), module=None)


@pytest.mark.django_db
def test_string_time_to_timestamp_ok():
    kvs = [
        {
            'time': '2w',
            'timestamp': relativedelta(weeks=2),
            'msg': '2 weeks',
        },
        {
            'time': '23d',
            'timestamp': relativedelta(days=23),
            'msg': '23 days',
        },
        {
            'time': '11m',
            'timestamp': relativedelta(months=11),
            'msg': '11 months',
        },
        {
            'time': '14y',
            'timestamp': relativedelta(years=14),
            'msg': '14 years',
        },
    ]
    for kv in kvs:
        cmd = Command()
        res = cmd.string_time_to_timestamp(kv['time'])
        assert kv['timestamp'] == res


@pytest.mark.django_db
def test_string_time_to_timestamp_invalid():
    kvs = [
        {
            'time': '2weeks',
            'msg': 'weeks instead of w',
        },
        {
            'time': '2days',
            'msg': 'days instead of d',
        },
        {
            'time': '23',
            'msg': 'no unit specified',
        },
        {
            'time': None,
            'msg': 'no value specified',
        },
        {
            'time': 'zigzag',
            'msg': 'random string specified',
        },
    ]
    for kv in kvs:
        cmd = Command()
        res = cmd.string_time_to_timestamp(kv['time'])
        assert res is None


@mock.patch('awx.main.management.commands.cleanup_facts.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_parameters_fail(mocker):
    # Mock run() just in case, but it should never get called because an error should be thrown
    mocker.patch('awx.main.management.commands.cleanup_facts.CleanupFacts.run')
    kvs = [
        {
            'older_than': '1week',
            'granularity': '1d',
            'msg': '--older_than invalid value "1week"',
        },
        {
            'older_than': '1d',
            'granularity': '1year',
            'msg': '--granularity invalid value "1year"',
        }
    ]
    for kv in kvs:
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(None, older_than=kv['older_than'], granularity=kv['granularity'])
        assert kv['msg'] in str(err.value)
