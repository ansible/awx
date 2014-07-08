__author__ = 'Matt Croydon, Mikhail Korobov, Pawel Tomasiewicz'
__version__ = (0, 7, 0)

from functools import partial
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

from django.db.models import Count
from django.db import DatabaseError, transaction
from django.conf import settings

from qsstats.utils import get_bounds, _to_datetime, _parse_interval, get_interval_sql, _remove_time
from qsstats import compat
from qsstats.exceptions import *

class QuerySetStats(object):
    """
    Generates statistics about a queryset using Django aggregates.  QuerySetStats
    is able to handle snapshots of data (for example this day, week, month, or
    year) or generate time series data suitable for graphing.
    """
    def __init__(self, qs=None, date_field=None, aggregate=None, today=None):
        self.qs = qs
        self.date_field = date_field
        self.aggregate = aggregate or Count('id')
        self.today = today or self.update_today()

    def _guess_engine(self):
        if hasattr(self.qs, 'db'): # django 1.2+
            engine_name = settings.DATABASES[self.qs.db]['ENGINE']
        else:
            engine_name = settings.DATABASE_ENGINE
        if 'mysql' in engine_name:
            return 'mysql'
        if 'postg' in engine_name: #postgres, postgis
            return 'postgresql'
        if 'sqlite' in engine_name:
            return 'sqlite'

    # Aggregates for a specific period of time

    def for_interval(self, interval, dt, date_field=None, aggregate=None):
        start, end = get_bounds(dt, interval)
        date_field = date_field or self.date_field
        kwargs = {'%s__range' % date_field : (start, end)}
        return self._aggregate(date_field, aggregate, kwargs)

    def this_interval(self, interval, date_field=None, aggregate=None):
        method = getattr(self, 'for_%s' % interval)
        return method(self.today, date_field, aggregate)

    # support for this_* and for_* methods
    def __getattr__(self, name):
        if name.startswith('for_'):
            return partial(self.for_interval, name[4:])
        if name.startswith('this_'):
            return partial(self.this_interval, name[5:])
        raise AttributeError

    def time_series(self, start, end=None, interval='days',
                    date_field=None, aggregate=None, engine=None):
        ''' Aggregate over time intervals '''

        end = end or self.today
        args = [start, end, interval, date_field, aggregate]
        engine = engine or self._guess_engine()
        sid = transaction.savepoint()
        try:
            return self._fast_time_series(*(args+[engine]))
        except (QuerySetStatsError, DatabaseError,):
            transaction.savepoint_rollback(sid)
            return self._slow_time_series(*args)

    def _slow_time_series(self, start, end, interval='days',
                          date_field=None, aggregate=None):
        ''' Aggregate over time intervals using 1 sql query for one interval '''

        num, interval = _parse_interval(interval)

        if interval not in ['minutes', 'hours',
                            'days', 'weeks',
                            'months', 'years'] or num != 1:
            raise InvalidInterval('Interval is currently not supported.')

        method = getattr(self, 'for_%s' % interval[:-1])

        stat_list = []
        dt, end = _to_datetime(start), _to_datetime(end)
        while dt <= end:
            value = method(dt, date_field, aggregate)
            stat_list.append((dt, value,))
            dt = dt + relativedelta(**{interval : 1})
        return stat_list

    def _fast_time_series(self, start, end, interval='days',
                          date_field=None, aggregate=None, engine=None):
        ''' Aggregate over time intervals using just 1 sql query '''

        date_field = date_field or self.date_field
        aggregate = aggregate or self.aggregate
        engine = engine or self._guess_engine()

        num, interval = _parse_interval(interval)

        start, _ = get_bounds(start, interval.rstrip('s'))
        _, end = get_bounds(end, interval.rstrip('s'))
        interval_sql = get_interval_sql(date_field, interval, engine)

        kwargs = {'%s__range' % date_field : (start, end)}
        aggregate_data = self.qs.extra(select = {'d': interval_sql}).\
                        filter(**kwargs).order_by().values('d').\
                        annotate(agg=aggregate)

        today = _remove_time(compat.now())
        def to_dt(d):
            if isinstance(d, basestring):
                return parse(d, yearfirst=True, default=today)
            return d

        data = dict((to_dt(item['d']), item['agg']) for item in aggregate_data)

        stat_list = []
        dt = start
        try:
            from django.utils.timezone import utc
            dt = dt.replace(tzinfo=utc)
            end = end.replace(tzinfo=utc)
        except ImportError:
            pass
        while dt < end:
            idx = 0
            value = 0
            for i in range(num):
                value = value + data.get(dt, 0)
                if i == 0:
                    stat_list.append((dt, value,))
                    idx = len(stat_list) - 1
                elif i == num - 1:
                    stat_list[idx] = (dt, value,)
                dt = dt + relativedelta(**{interval : 1})

        return stat_list

    # Aggregate totals using a date or datetime as a pivot

    def until(self, dt, date_field=None, aggregate=None):
        return self.pivot(dt, 'lte', date_field, aggregate)

    def until_now(self, date_field=None, aggregate=None):
        return self.pivot(compat.now(), 'lte', date_field, aggregate)

    def after(self, dt, date_field=None, aggregate=None):
        return self.pivot(dt, 'gte', date_field, aggregate)

    def after_now(self, date_field=None, aggregate=None):
        return self.pivot(compat.now(), 'gte', date_field, aggregate)

    def pivot(self, dt, operator=None, date_field=None, aggregate=None):
        operator = operator or self.operator
        if operator not in ['lt', 'lte', 'gt', 'gte']:
            raise InvalidOperator("Please provide a valid operator.")

        kwargs = {'%s__%s' % (date_field or self.date_field, operator) : dt}
        return self._aggregate(date_field, aggregate, kwargs)

    # Utility functions
    def update_today(self):
        _now = compat.now()
        self.today = _remove_time(_now)
        return self.today

    def _aggregate(self, date_field=None, aggregate=None, filter=None):
        date_field = date_field or self.date_field
        aggregate = aggregate or self.aggregate

        if not date_field:
            raise DateFieldMissing("Please provide a date_field.")

        if self.qs is None:
            raise QuerySetMissing("Please provide a queryset.")

        agg = self.qs.filter(**filter).aggregate(agg=aggregate)
        return agg['agg']
