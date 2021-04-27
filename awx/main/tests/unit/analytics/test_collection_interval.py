import logging
import pytest

from django.utils.timezone import now, timedelta

from awx.main.analytics.core import calculate_collection_interval

# This is some bullshit.
logger = logging.getLogger('awx.main.analytics')
logger.propagate = True

epsilon = timedelta(minutes=1)


class TestIntervalWithSinceAndUntil:
    @pytest.mark.parametrize('gather', [None, 2, 6])
    def test_ok(self, caplog, settings, gather):
        _now = now()
        _prior = _now - timedelta(weeks=gather) if gather is not None else None
        until = _now
        since = until - timedelta(weeks=3)
        settings.AUTOMATION_ANALYTICS_LAST_GATHER = _prior

        new_since, new_until, last_gather = calculate_collection_interval(since, until)
        assert new_since == since
        assert new_until == until

        # 1 log message, if LAST_GATHER was more than 4 weeks ago
        expected = 1 if gather and gather > 4 else 0
        assert len(caplog.records) == expected
        assert sum(1 for msg in caplog.messages if "more than 4 weeks prior" in msg) == expected

        # last_gather is always set to something even if LAST_GATHER was empty
        assert last_gather is not None
        assert abs(until - last_gather - timedelta(weeks=gather if gather and gather <= 4 else 4)) < epsilon

    def test_both_in_future(self, caplog):
        since = now() + timedelta(weeks=1)
        until = since + timedelta(weeks=1)

        with pytest.raises(ValueError):
            calculate_collection_interval(since, until)

        # log message each for `since` and `until` getting chopped, then another for the empty interval
        assert len(caplog.records) == 3
        assert sum(1 for msg in caplog.messages if "is in the future" in msg) == 2
        assert sum(1 for msg in caplog.messages if "later than the end" in msg) == 1

    def test_until_in_future(self, caplog):
        _now = now()
        since = _now - timedelta(weeks=1)
        until = _now + timedelta(weeks=1)

        new_since, new_until, _ = calculate_collection_interval(since, until)
        assert new_since == since
        assert abs(_now - new_until) < epsilon  # `until` gets truncated to now()

        # log message for `until` getting chopped
        assert len(caplog.records) == 1
        assert sum(1 for msg in caplog.messages if "is in the future" in msg) == 1

    def test_interval_too_large(self, caplog):
        until = now()
        since = until - timedelta(weeks=5)

        new_since, new_until, _ = calculate_collection_interval(since, until)
        # interval is 4 weeks counting forward from explicit `since`
        assert new_since == since
        assert new_until == since + timedelta(weeks=4)

        # log message for `until` getting chopped
        assert len(caplog.records) == 1
        assert sum(1 for msg in caplog.messages if "greater than 4 weeks from start" in msg) == 1

    def test_reversed(self, caplog):
        since = now()
        until = since - timedelta(weeks=3)

        with pytest.raises(ValueError):
            calculate_collection_interval(since, until)

        # log message for the empty interval
        assert len(caplog.records) == 1
        assert sum(1 for msg in caplog.messages if "later than the end" in msg) == 1


class TestIntervalWithSinceOnly:
    @pytest.mark.parametrize('gather', [None, 2, 6])
    def test_ok(self, caplog, settings, gather):
        _now = now()
        _prior = _now - timedelta(weeks=gather) if gather is not None else None
        since = _now - timedelta(weeks=2)
        until = None  # until is going to wind up being effectively now.
        settings.AUTOMATION_ANALYTICS_LAST_GATHER = _prior

        new_since, new_until, last_gather = calculate_collection_interval(since, until)
        # `since` is only 2 weeks back, so now() is within the 4-week cutoff and can be used for `until`
        assert new_since == since
        assert abs(new_until - _now) < epsilon

        # 1 log message, if LAST_GATHER was more than 4 weeks ago
        expected = 1 if gather and gather > 4 else 0
        assert len(caplog.records) == expected
        assert sum(1 for msg in caplog.messages if "more than 4 weeks prior" in msg) == expected

        # last_gather is always set to something even if LAST_GATHER was empty
        assert last_gather is not None
        assert abs(_now - last_gather - timedelta(weeks=gather if gather and gather <= 4 else 4)) < epsilon

    def test_since_more_than_4_weeks_before_now(self, caplog):
        since = now() - timedelta(weeks=5)
        until = None  # until is going to wind up being effectively now.

        new_since, new_until, last_gather = calculate_collection_interval(since, until)
        # interval is 4 weeks counting forward from explicit `since`
        assert new_since == since
        assert new_until == since + timedelta(weeks=4)

        # no logs, since no explicit parameters were truncated or adjusted
        assert len(caplog.records) == 0

    def test_since_in_future(self, caplog):
        since = now() + timedelta(weeks=1)
        until = None

        with pytest.raises(ValueError):
            calculate_collection_interval(since, until)

        # log message for `since` getting chopped, and another for the empty interval
        assert len(caplog.records) == 2
        assert sum(1 for msg in caplog.messages if "is in the future" in msg) == 1
        assert sum(1 for msg in caplog.messages if "later than the end" in msg) == 1


class TestIntervalWithUntilOnly:
    @pytest.mark.parametrize('gather', [None, 2, 6])
    def test_ok(self, caplog, settings, gather):
        _now = now()
        _prior = _now - timedelta(weeks=gather) if gather is not None else None
        since = None
        until = _now - timedelta(weeks=1)
        settings.AUTOMATION_ANALYTICS_LAST_GATHER = _prior

        new_since, new_until, last_gather = calculate_collection_interval(since, until)
        assert new_since is None  # this allows LAST_ENTRIES[key] to be the fallback
        assert new_until == until

        # last_gather is always set to something even if LAST_GATHER was empty
        assert last_gather is not None
        # since `until` is 1 week ago, the 4-week cutoff is 5 weeks ago
        assert abs(_now - last_gather - timedelta(weeks=gather if gather and gather <= 5 else 5)) < epsilon

        # 1 log message for LAST_GATHER, if it was more than 4 weeks before `until`
        expected = 1 if gather and gather > 5 else 0
        assert len(caplog.records) == expected
        assert sum(1 for msg in caplog.messages if "more than 4 weeks prior" in msg) == expected

    def test_until_in_future(self, caplog):
        _now = now()
        since = None
        until = _now + timedelta(weeks=1)

        new_since, new_until, _ = calculate_collection_interval(since, until)
        assert new_since is None  # this allows LAST_ENTRIES[key] to be the fallback
        assert abs(new_until - _now) < epsilon  # `until` gets truncated to now()

        # log message for `until` getting chopped
        assert len(caplog.records) == 1
        assert sum(1 for msg in caplog.messages if "is in the future" in msg) == 1


class TestIntervalWithNoParams:
    @pytest.mark.parametrize('gather', [None, 2, 6])
    def test_ok(self, caplog, settings, gather):
        _now = now()
        _prior = _now - timedelta(weeks=gather) if gather is not None else None
        since, until = None, None
        settings.AUTOMATION_ANALYTICS_LAST_GATHER = _prior

        new_since, new_until, last_gather = calculate_collection_interval(since, until)
        assert new_since is None  # this allows LAST_ENTRIES[key] to be the fallback
        assert abs(new_until - _now) < epsilon  # `until` defaults to now()

        # last_gather is always set to something even if LAST_GATHER was empty
        assert last_gather is not None
        assert abs(_now - last_gather - timedelta(weeks=gather if gather and gather <= 4 else 4)) < epsilon

        # 1 log message for LAST_GATHER, if it was more than 4 weeks before now
        expected = 1 if gather and gather > 4 else 0
        assert len(caplog.records) == expected
        assert sum(1 for msg in caplog.messages if "more than 4 weeks prior" in msg) == expected
