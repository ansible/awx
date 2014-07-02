import datetime
import re
from dateutil.relativedelta import relativedelta, MO
from qsstats.exceptions import InvalidInterval, UnsupportedEngine
from qsstats import compat

def _remove_time(dt):
    tzinfo = getattr(dt, 'tzinfo', compat.now().tzinfo)
    return datetime.datetime(dt.year, dt.month, dt.day, tzinfo=tzinfo)

def _to_datetime(dt):
    if isinstance(dt, datetime.datetime):
        return dt
    return _remove_time(dt)

def _parse_interval(interval):
    num = 1
    match = re.match('(\d+)([A-Za-z]+)', interval)

    if match:
        num = int(match.group(1))
        interval = match.group(2)
    return num, interval

def get_bounds(dt, interval):
    ''' Returns interval bounds the datetime is in. '''

    day = _to_datetime(_remove_time(dt))
    dt = _to_datetime(dt)

    if interval == 'minute':
        begin = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, tzinfo=dt.tzinfo)
        end = begin + relativedelta(minutes=1)
    elif interval == 'hour':
        begin = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=dt.tzinfo)
        end = begin + relativedelta(hours=1)
    elif interval == 'day':
        begin = day
        end = day + relativedelta(days=1)
    elif interval == 'week':
        begin = day - relativedelta(weekday=MO(-1))
        end = begin + datetime.timedelta(days=7)
    elif interval == 'month':
        begin = datetime.datetime(dt.year, dt.month, 1, tzinfo=dt.tzinfo)
        end = begin + relativedelta(months=1)
    elif interval == 'year':
        begin = datetime.datetime(dt.year, 1, 1, tzinfo=dt.tzinfo)
        end = datetime.datetime(dt.year+1, 1, 1, tzinfo=dt.tzinfo)
    else:
        raise InvalidInterval('Inverval not supported.')
    end = end - relativedelta(microseconds=1)
    return begin, end


def get_interval_sql(date_field, interval, engine):
    ''' Returns SQL clause that calculates the beginning of interval
        date_field belongs to.
    '''

    SQL = {
        'mysql': {
            'minutes': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-%%d %%H:%%i')",
            'hours': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-%%d %%H:00')",
            'days': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-%%d')",
            'weeks': "DATE_FORMAT(DATE_SUB(`"+date_field+"`, INTERVAL(WEEKDAY(`"+date_field+"`)) DAY), '%%Y-%%m-%%d')",
            'months': "DATE_FORMAT(`" + date_field +"`, '%%Y-%%m-01')",
            'years': "DATE_FORMAT(`" + date_field +"`, '%%Y-01-01')",
        },
        'postgresql': {
            'minutes': "date_trunc('minute', %s)" % date_field,
            'hours': "date_trunc('hour', %s)" % date_field,
            'days': "date_trunc('day', %s)" % date_field,
            'weeks': "date_trunc('week', %s)" % date_field,
            'months': "date_trunc('month', %s)" % date_field,
            'years': "date_trunc('year', %s)" % date_field,
        },
        'sqlite': {
            'minutes': "strftime('%%Y-%%m-%%d %%H:%%M', `" + date_field + "`)",
            'hours': "strftime('%%Y-%%m-%%d %%H:00', `" + date_field + "`)",
            'days': "strftime('%%Y-%%m-%%d', `" + date_field + "`)",
            'weeks':  "strftime('%%Y-%%m-%%d', julianday(`" + date_field + "`) - strftime('%%w', `" + date_field + "`) + 1)",
            'months': "strftime('%%Y-%%m-01', `" + date_field + "`)",          
            'years': "strftime('%%Y-01-01', `" + date_field + "`)",                     
        },
        
    }

    try:
        engine_sql = SQL[engine]
    except KeyError:
        msg = '%s DB engine is not supported. Supported engines are: %s' % (engine, ", ".join(SQL.keys()))
        raise UnsupportedEngine(msg)

    try:
        return engine_sql[interval]
    except KeyError:
        raise InvalidInterval('Interval is not supported for %s DB backend.' % engine)

