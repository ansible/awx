from __future__ import absolute_import
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from qsstats import QuerySetStats, InvalidInterval, DateFieldMissing, QuerySetMissing
from qsstats import compat
from .utils import _remove_time

class QuerySetStatsTestCase(TestCase):
    def test_basic_today(self):
        # We'll be making sure that this user is found
        u1 = User.objects.create_user('u1', 'u1@example.com')
        # And that this user is not
        u2 = User.objects.create_user('u2', 'u2@example.com')
        u2.is_active = False
        u2.save()

        # Create a QuerySet and QuerySetStats
        qs = User.objects.filter(is_active=True)
        qss = QuerySetStats(qs, 'date_joined')

        # We should only see a single user
        self.assertEqual(qss.this_day(), 1)

    def assertTimeSeriesWorks(self, today):
        seven_days_ago = today - datetime.timedelta(days=7)
        for j in range(1,8):
            for i in range(0,j):
                u = User.objects.create_user('p-%s-%s' % (j, i), 'p%s-%s@example.com' % (j, i))
                u.date_joined = today - datetime.timedelta(days=i)
                u.save()
        qs = User.objects.all()
        qss = QuerySetStats(qs, 'date_joined')
        time_series = qss.time_series(seven_days_ago, today)
        self.assertEqual([t[1] for t in time_series], [0, 1, 2, 3, 4, 5, 6, 7])

    def test_time_series(self):
        _now = compat.now()
        today = _remove_time(_now)
        self.assertTimeSeriesWorks(today)

    def test_time_series_naive(self):
        self.assertTimeSeriesWorks(datetime.date.today())

    def test_time_series_weeks(self):
        day = datetime.date(year=2013, month=4, day=5)

        u = User.objects.create_user('user', 'user@example.com')
        u.date_joined = day
        u.save()

        qs = User.objects.all()
        qss = QuerySetStats(qs, 'date_joined')
        qss.time_series(day - datetime.timedelta(days=30), day, interval='weeks')

    def test_until(self):
        now = compat.now()
        today = _remove_time(now)
        yesterday = today - datetime.timedelta(days=1)

        u = User.objects.create_user('u', 'u@example.com')
        u.date_joined = today
        u.save()

        qs = User.objects.all()
        qss = QuerySetStats(qs, 'date_joined')

        self.assertEqual(qss.until(now), 1)
        self.assertEqual(qss.until(today), 1)
        self.assertEqual(qss.until(yesterday), 0)
        self.assertEqual(qss.until_now(), 1)

    def test_after(self):
        now = compat.now()
        today = _remove_time(now)
        tomorrow = today + datetime.timedelta(days=1)

        u = User.objects.create_user('u', 'u@example.com')
        u.date_joined = today
        u.save()

        qs = User.objects.all()
        qss = QuerySetStats(qs, 'date_joined')

        self.assertEqual(qss.after(today), 1)
        self.assertEqual(qss.after(now), 0)
        u.date_joined=tomorrow
        u.save()
        self.assertEqual(qss.after(now), 1)

    # MC_TODO: aggregate_field tests

    def test_query_set_missing(self):
        qss = QuerySetStats(date_field='foo')
        for method in ['this_day', 'this_month', 'this_year']:
            self.assertRaises(QuerySetMissing, getattr(qss, method))

    def test_date_field_missing(self):
        qss = QuerySetStats(User.objects.all())
        for method in ['this_day', 'this_month', 'this_year']:
            self.assertRaises(DateFieldMissing, getattr(qss, method))

    def test_invalid_interval(self):
        qss = QuerySetStats(User.objects.all(), 'date_joined')
        def _invalid():
            qss.time_series(qss.today, qss.today, interval='monkeys')
        self.assertRaises(InvalidInterval, _invalid)
