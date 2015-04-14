# Copyright 2011 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import calendar
import datetime
import time

import iso8601
import mock
from oslotest import base as test_base
from testtools import matchers

from oslo_utils import timeutils


def monotonic_iter(start=0, incr=0.05):
    while True:
        yield start
        start += incr


class TimeUtilsTest(test_base.BaseTestCase):

    def setUp(self):
        super(TimeUtilsTest, self).setUp()
        self.skynet_self_aware_time_str = '1997-08-29T06:14:00Z'
        self.skynet_self_aware_time_ms_str = '1997-08-29T06:14:00.000123Z'
        self.skynet_self_aware_time = datetime.datetime(1997, 8, 29, 6, 14, 0)
        self.skynet_self_aware_ms_time = datetime.datetime(
            1997, 8, 29, 6, 14, 0, 123)
        self.one_minute_before = datetime.datetime(1997, 8, 29, 6, 13, 0)
        self.one_minute_after = datetime.datetime(1997, 8, 29, 6, 15, 0)
        self.skynet_self_aware_time_perfect_str = '1997-08-29T06:14:00.000000'
        self.skynet_self_aware_time_perfect = datetime.datetime(1997, 8, 29,
                                                                6, 14, 0)
        self.addCleanup(timeutils.clear_time_override)

    def test_isotime(self):
        with mock.patch('datetime.datetime') as datetime_mock:
            datetime_mock.utcnow.return_value = self.skynet_self_aware_time
            dt = timeutils.isotime()
            self.assertEqual(dt, self.skynet_self_aware_time_str)

    def test_isotimei_micro_second_precision(self):
        with mock.patch('datetime.datetime') as datetime_mock:
            datetime_mock.utcnow.return_value = self.skynet_self_aware_ms_time
            dt = timeutils.isotime(subsecond=True)
            self.assertEqual(dt, self.skynet_self_aware_time_ms_str)

    def test_parse_isotime(self):
        expect = timeutils.parse_isotime(self.skynet_self_aware_time_str)
        skynet_self_aware_time_utc = self.skynet_self_aware_time.replace(
            tzinfo=iso8601.iso8601.UTC)
        self.assertEqual(skynet_self_aware_time_utc, expect)

    def test_parse_isotime_micro_second_precision(self):
        expect = timeutils.parse_isotime(self.skynet_self_aware_time_ms_str)
        skynet_self_aware_time_ms_utc = self.skynet_self_aware_ms_time.replace(
            tzinfo=iso8601.iso8601.UTC)
        self.assertEqual(skynet_self_aware_time_ms_utc, expect)

    def test_strtime(self):
        expect = timeutils.strtime(self.skynet_self_aware_time_perfect)
        self.assertEqual(self.skynet_self_aware_time_perfect_str, expect)

    def test_parse_strtime(self):
        perfect_time_format = self.skynet_self_aware_time_perfect_str
        expect = timeutils.parse_strtime(perfect_time_format)
        self.assertEqual(self.skynet_self_aware_time_perfect, expect)

    def test_strtime_and_back(self):
        orig_t = datetime.datetime(1997, 8, 29, 6, 14, 0)
        s = timeutils.strtime(orig_t)
        t = timeutils.parse_strtime(s)
        self.assertEqual(orig_t, t)

    def _test_is_older_than(self, fn):
        strptime = datetime.datetime.strptime
        with mock.patch('datetime.datetime') as datetime_mock:
            datetime_mock.utcnow.return_value = self.skynet_self_aware_time
            datetime_mock.strptime = strptime
            expect_true = timeutils.is_older_than(fn(self.one_minute_before),
                                                  59)
            self.assertTrue(expect_true)
            expect_false = timeutils.is_older_than(fn(self.one_minute_before),
                                                   60)
            self.assertFalse(expect_false)
            expect_false = timeutils.is_older_than(fn(self.one_minute_before),
                                                   61)
            self.assertFalse(expect_false)

    def test_is_older_than_datetime(self):
        self._test_is_older_than(lambda x: x)

    def test_is_older_than_str(self):
        self._test_is_older_than(timeutils.strtime)

    def test_is_older_than_aware(self):
        """Tests sending is_older_than an 'aware' datetime."""
        self._test_is_older_than(lambda x: x.replace(
            tzinfo=iso8601.iso8601.UTC))

    def _test_is_newer_than(self, fn):
        strptime = datetime.datetime.strptime
        with mock.patch('datetime.datetime') as datetime_mock:
            datetime_mock.utcnow.return_value = self.skynet_self_aware_time
            datetime_mock.strptime = strptime
            expect_true = timeutils.is_newer_than(fn(self.one_minute_after),
                                                  59)
            self.assertTrue(expect_true)
            expect_false = timeutils.is_newer_than(fn(self.one_minute_after),
                                                   60)
            self.assertFalse(expect_false)
            expect_false = timeutils.is_newer_than(fn(self.one_minute_after),
                                                   61)
            self.assertFalse(expect_false)

    def test_is_newer_than_datetime(self):
        self._test_is_newer_than(lambda x: x)

    def test_is_newer_than_str(self):
        self._test_is_newer_than(timeutils.strtime)

    def test_is_newer_than_aware(self):
        """Tests sending is_newer_than an 'aware' datetime."""
        self._test_is_newer_than(lambda x: x.replace(
            tzinfo=iso8601.iso8601.UTC))

    def test_set_time_override_using_default(self):
        now = timeutils.utcnow_ts()

        # NOTE(kgriffs): Normally it's bad form to sleep in a unit test,
        # but this is the only way to test that set_time_override defaults
        # to setting the override to the current time.
        time.sleep(1)

        timeutils.set_time_override()
        overriden_now = timeutils.utcnow_ts()
        self.assertThat(now, matchers.LessThan(overriden_now))

    def test_utcnow_ts(self):
        skynet_self_aware_ts = 872835240
        skynet_dt = datetime.datetime.utcfromtimestamp(skynet_self_aware_ts)
        self.assertEqual(self.skynet_self_aware_time, skynet_dt)

        # NOTE(kgriffs): timeutils.utcnow_ts() uses time.time()
        # IFF time override is not set.
        with mock.patch('time.time') as time_mock:
            time_mock.return_value = skynet_self_aware_ts
            ts = timeutils.utcnow_ts()
            self.assertEqual(ts, skynet_self_aware_ts)

        timeutils.set_time_override(skynet_dt)
        ts = timeutils.utcnow_ts()
        self.assertEqual(ts, skynet_self_aware_ts)

    def test_utcnow(self):
        timeutils.set_time_override(mock.sentinel.utcnow)
        self.assertEqual(timeutils.utcnow(), mock.sentinel.utcnow)

        timeutils.clear_time_override()
        self.assertFalse(timeutils.utcnow() == mock.sentinel.utcnow)

        self.assertTrue(timeutils.utcnow())

    def test_advance_time_delta(self):
        timeutils.set_time_override(self.one_minute_before)
        timeutils.advance_time_delta(datetime.timedelta(seconds=60))
        self.assertEqual(timeutils.utcnow(), self.skynet_self_aware_time)

    def test_advance_time_seconds(self):
        timeutils.set_time_override(self.one_minute_before)
        timeutils.advance_time_seconds(60)
        self.assertEqual(timeutils.utcnow(), self.skynet_self_aware_time)

    def test_marshall_time(self):
        now = timeutils.utcnow()
        binary = timeutils.marshall_now(now)
        backagain = timeutils.unmarshall_time(binary)
        self.assertEqual(now, backagain)

    def test_delta_seconds(self):
        before = timeutils.utcnow()
        after = before + datetime.timedelta(days=7, seconds=59,
                                            microseconds=123456)
        self.assertAlmostEquals(604859.123456,
                                timeutils.delta_seconds(before, after))

    def test_total_seconds(self):
        delta = datetime.timedelta(days=1, hours=2, minutes=3, seconds=4.5)
        self.assertAlmostEquals(93784.5,
                                timeutils.total_seconds(delta))

    def test_iso8601_from_timestamp(self):
        utcnow = timeutils.utcnow()
        iso = timeutils.isotime(utcnow)
        ts = calendar.timegm(utcnow.timetuple())
        self.assertEqual(iso, timeutils.iso8601_from_timestamp(ts))

    def test_iso8601_from_timestamp_ms(self):
        ts = timeutils.utcnow_ts(microsecond=True)
        utcnow = datetime.datetime.utcfromtimestamp(ts)
        iso = timeutils.isotime(utcnow, subsecond=True)
        self.assertEqual(iso, timeutils.iso8601_from_timestamp(ts, True))

    def test_is_soon(self):
        expires = timeutils.utcnow() + datetime.timedelta(minutes=5)
        self.assertFalse(timeutils.is_soon(expires, 120))
        self.assertTrue(timeutils.is_soon(expires, 300))
        self.assertTrue(timeutils.is_soon(expires, 600))

        with mock.patch('datetime.datetime') as datetime_mock:
            datetime_mock.utcnow.return_value = self.skynet_self_aware_time
            expires = timeutils.utcnow()
            self.assertTrue(timeutils.is_soon(expires, 0))


class TestIso8601Time(test_base.BaseTestCase):

    def _instaneous(self, timestamp, yr, mon, day, hr, minute, sec, micro):
        self.assertEqual(timestamp.year, yr)
        self.assertEqual(timestamp.month, mon)
        self.assertEqual(timestamp.day, day)
        self.assertEqual(timestamp.hour, hr)
        self.assertEqual(timestamp.minute, minute)
        self.assertEqual(timestamp.second, sec)
        self.assertEqual(timestamp.microsecond, micro)

    def _do_test(self, time_str, yr, mon, day, hr, minute, sec, micro, shift):
        DAY_SECONDS = 24 * 60 * 60
        timestamp = timeutils.parse_isotime(time_str)
        self._instaneous(timestamp, yr, mon, day, hr, minute, sec, micro)
        offset = timestamp.tzinfo.utcoffset(None)
        self.assertEqual(offset.seconds + offset.days * DAY_SECONDS, shift)

    def test_zulu(self):
        time_str = '2012-02-14T20:53:07Z'
        self._do_test(time_str, 2012, 2, 14, 20, 53, 7, 0, 0)

    def test_zulu_micros(self):
        time_str = '2012-02-14T20:53:07.123Z'
        self._do_test(time_str, 2012, 2, 14, 20, 53, 7, 123000, 0)

    def test_offset_east(self):
        time_str = '2012-02-14T20:53:07+04:30'
        offset = 4.5 * 60 * 60
        self._do_test(time_str, 2012, 2, 14, 20, 53, 7, 0, offset)

    def test_offset_east_micros(self):
        time_str = '2012-02-14T20:53:07.42+04:30'
        offset = 4.5 * 60 * 60
        self._do_test(time_str, 2012, 2, 14, 20, 53, 7, 420000, offset)

    def test_offset_west(self):
        time_str = '2012-02-14T20:53:07-05:30'
        offset = -5.5 * 60 * 60
        self._do_test(time_str, 2012, 2, 14, 20, 53, 7, 0, offset)

    def test_offset_west_micros(self):
        time_str = '2012-02-14T20:53:07.654321-05:30'
        offset = -5.5 * 60 * 60
        self._do_test(time_str, 2012, 2, 14, 20, 53, 7, 654321, offset)

    def test_compare(self):
        zulu = timeutils.parse_isotime('2012-02-14T20:53:07')
        east = timeutils.parse_isotime('2012-02-14T20:53:07-01:00')
        west = timeutils.parse_isotime('2012-02-14T20:53:07+01:00')
        self.assertTrue(east > west)
        self.assertTrue(east > zulu)
        self.assertTrue(zulu > west)

    def test_compare_micros(self):
        zulu = timeutils.parse_isotime('2012-02-14T20:53:07.6544')
        east = timeutils.parse_isotime('2012-02-14T19:53:07.654321-01:00')
        west = timeutils.parse_isotime('2012-02-14T21:53:07.655+01:00')
        self.assertTrue(east < west)
        self.assertTrue(east < zulu)
        self.assertTrue(zulu < west)

    def test_zulu_roundtrip(self):
        time_str = '2012-02-14T20:53:07Z'
        zulu = timeutils.parse_isotime(time_str)
        self.assertEqual(zulu.tzinfo, iso8601.iso8601.UTC)
        self.assertEqual(timeutils.isotime(zulu), time_str)

    def test_east_roundtrip(self):
        time_str = '2012-02-14T20:53:07-07:00'
        east = timeutils.parse_isotime(time_str)
        self.assertEqual(east.tzinfo.tzname(None), '-07:00')
        self.assertEqual(timeutils.isotime(east), time_str)

    def test_west_roundtrip(self):
        time_str = '2012-02-14T20:53:07+11:30'
        west = timeutils.parse_isotime(time_str)
        self.assertEqual(west.tzinfo.tzname(None), '+11:30')
        self.assertEqual(timeutils.isotime(west), time_str)

    def test_now_roundtrip(self):
        time_str = timeutils.isotime()
        now = timeutils.parse_isotime(time_str)
        self.assertEqual(now.tzinfo, iso8601.iso8601.UTC)
        self.assertEqual(timeutils.isotime(now), time_str)

    def test_zulu_normalize(self):
        time_str = '2012-02-14T20:53:07Z'
        zulu = timeutils.parse_isotime(time_str)
        normed = timeutils.normalize_time(zulu)
        self._instaneous(normed, 2012, 2, 14, 20, 53, 7, 0)

    def test_east_normalize(self):
        time_str = '2012-02-14T20:53:07-07:00'
        east = timeutils.parse_isotime(time_str)
        normed = timeutils.normalize_time(east)
        self._instaneous(normed, 2012, 2, 15, 3, 53, 7, 0)

    def test_west_normalize(self):
        time_str = '2012-02-14T20:53:07+21:00'
        west = timeutils.parse_isotime(time_str)
        normed = timeutils.normalize_time(west)
        self._instaneous(normed, 2012, 2, 13, 23, 53, 7, 0)

    def test_normalize_aware_to_naive(self):
        dt = datetime.datetime(2011, 2, 14, 20, 53, 7)
        time_str = '2011-02-14T20:53:07+21:00'
        aware = timeutils.parse_isotime(time_str)
        naive = timeutils.normalize_time(aware)
        self.assertTrue(naive < dt)

    def test_normalize_zulu_aware_to_naive(self):
        dt = datetime.datetime(2011, 2, 14, 20, 53, 7)
        time_str = '2011-02-14T19:53:07Z'
        aware = timeutils.parse_isotime(time_str)
        naive = timeutils.normalize_time(aware)
        self.assertTrue(naive < dt)

    def test_normalize_naive(self):
        dt = datetime.datetime(2011, 2, 14, 20, 53, 7)
        dtn = datetime.datetime(2011, 2, 14, 19, 53, 7)
        naive = timeutils.normalize_time(dtn)
        self.assertTrue(naive < dt)


class StopWatchTest(test_base.BaseTestCase):
    def test_leftover_no_duration(self):
        watch = timeutils.StopWatch()
        watch.start()
        self.assertRaises(RuntimeError, watch.leftover)
        self.assertRaises(RuntimeError, watch.leftover, return_none=False)
        self.assertIsNone(watch.leftover(return_none=True))

    def test_no_states(self):
        watch = timeutils.StopWatch()
        self.assertRaises(RuntimeError, watch.stop)
        self.assertRaises(RuntimeError, watch.resume)

    def test_bad_expiry(self):
        self.assertRaises(ValueError, timeutils.StopWatch, -1)

    @mock.patch('oslo_utils.timeutils.now')
    def test_backwards(self, mock_now):
        mock_now.side_effect = [0, 0.5, -1.0, -1.0]
        watch = timeutils.StopWatch(0.1)
        watch.start()
        self.assertTrue(watch.expired())
        self.assertFalse(watch.expired())
        self.assertEqual(0.0, watch.elapsed())

    @mock.patch('oslo_utils.timeutils.now')
    def test_expiry(self, mock_now):
        mock_now.side_effect = monotonic_iter(incr=0.2)
        watch = timeutils.StopWatch(0.1)
        watch.start()
        self.assertTrue(watch.expired())

    @mock.patch('oslo_utils.timeutils.now')
    def test_not_expired(self, mock_now):
        mock_now.side_effect = monotonic_iter()
        watch = timeutils.StopWatch(0.1)
        watch.start()
        self.assertFalse(watch.expired())

    def test_has_started_stopped(self):
        watch = timeutils.StopWatch()
        self.assertFalse(watch.has_started())
        self.assertFalse(watch.has_stopped())
        watch.start()

        self.assertTrue(watch.has_started())
        self.assertFalse(watch.has_stopped())

        watch.stop()
        self.assertTrue(watch.has_stopped())
        self.assertFalse(watch.has_started())

    def test_no_expiry(self):
        watch = timeutils.StopWatch(0.1)
        self.assertRaises(RuntimeError, watch.expired)

    @mock.patch('oslo_utils.timeutils.now')
    def test_elapsed(self, mock_now):
        mock_now.side_effect = monotonic_iter(incr=0.2)
        watch = timeutils.StopWatch()
        watch.start()
        matcher = matchers.GreaterThan(0.19)
        self.assertThat(watch.elapsed(), matcher)

    def test_no_elapsed(self):
        watch = timeutils.StopWatch()
        self.assertRaises(RuntimeError, watch.elapsed)

    def test_no_leftover(self):
        watch = timeutils.StopWatch()
        self.assertRaises(RuntimeError, watch.leftover)
        watch = timeutils.StopWatch(1)
        self.assertRaises(RuntimeError, watch.leftover)

    @mock.patch('oslo_utils.timeutils.now')
    def test_pause_resume(self, mock_now):
        mock_now.side_effect = monotonic_iter()
        watch = timeutils.StopWatch()
        watch.start()
        watch.stop()
        elapsed = watch.elapsed()
        self.assertAlmostEqual(elapsed, watch.elapsed())
        watch.resume()
        self.assertNotEqual(elapsed, watch.elapsed())

    @mock.patch('oslo_utils.timeutils.now')
    def test_context_manager(self, mock_now):
        mock_now.side_effect = monotonic_iter()
        with timeutils.StopWatch() as watch:
            pass
        matcher = matchers.GreaterThan(0.04)
        self.assertThat(watch.elapsed(), matcher)

    @mock.patch('oslo_utils.timeutils.now')
    def test_context_manager_splits(self, mock_now):
        mock_now.side_effect = monotonic_iter()
        with timeutils.StopWatch() as watch:
            time.sleep(0.01)
            watch.split()
        self.assertRaises(RuntimeError, watch.split)
        self.assertEqual(1, len(watch.splits))

    def test_splits_stopped(self):
        watch = timeutils.StopWatch()
        watch.start()
        watch.split()
        watch.stop()
        self.assertRaises(RuntimeError, watch.split)

    def test_splits_never_started(self):
        watch = timeutils.StopWatch()
        self.assertRaises(RuntimeError, watch.split)

    @mock.patch('oslo_utils.timeutils.now')
    def test_splits(self, mock_now):
        mock_now.side_effect = monotonic_iter()

        watch = timeutils.StopWatch()
        watch.start()
        self.assertEqual(0, len(watch.splits))

        watch.split()
        self.assertEqual(1, len(watch.splits))
        self.assertEqual(watch.splits[0].elapsed,
                         watch.splits[0].length)

        watch.split()
        splits = watch.splits
        self.assertEqual(2, len(splits))
        self.assertNotEqual(splits[0].elapsed, splits[1].elapsed)
        self.assertEqual(splits[1].length,
                         splits[1].elapsed - splits[0].elapsed)

        watch.stop()
        self.assertEqual(2, len(watch.splits))

        watch.start()
        self.assertEqual(0, len(watch.splits))

    @mock.patch('oslo_utils.timeutils.now')
    def test_elapsed_maximum(self, mock_now):
        mock_now.side_effect = [0, 1] + ([11] * 4)

        watch = timeutils.StopWatch()
        watch.start()
        self.assertEqual(1, watch.elapsed())

        self.assertEqual(11, watch.elapsed())
        self.assertEqual(1, watch.elapsed(maximum=1))

        watch.stop()
        self.assertEqual(11, watch.elapsed())
        self.assertEqual(11, watch.elapsed())
        self.assertEqual(0, watch.elapsed(maximum=-1))
