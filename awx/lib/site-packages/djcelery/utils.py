# -- XXX This module must not use translation as that causes
# -- a recursive loader import!
from __future__ import absolute_import

from datetime import datetime

from django.conf import settings

# Database-related exceptions.
from django.db import DatabaseError
try:
    import MySQLdb as mysql
    _my_database_errors = (mysql.DatabaseError,
                           mysql.InterfaceError,
                           mysql.OperationalError)
except ImportError:
    _my_database_errors = ()      # noqa
try:
    import psycopg2 as pg
    _pg_database_errors = (pg.DatabaseError,
                           pg.InterfaceError,
                           pg.OperationalError)
except ImportError:
    _pg_database_errors = ()      # noqa
try:
    import sqlite3
    _lite_database_errors = (sqlite3.DatabaseError,
                             sqlite3.InterfaceError,
                             sqlite3.OperationalError)
except ImportError:
    _lite_database_errors = ()    # noqa
try:
    import cx_Oracle as oracle
    _oracle_database_errors = (oracle.DatabaseError,
                               oracle.InterfaceError,
                               oracle.OperationalError)
except ImportError:
    _oracle_database_errors = ()  # noqa

DATABASE_ERRORS = ((DatabaseError, ) +
                   _my_database_errors +
                   _pg_database_errors +
                   _lite_database_errors +
                   _oracle_database_errors)


try:
    from django.utils import timezone
    is_aware = timezone.is_aware

    # see Issue #222
    now_localtime = getattr(timezone, 'template_localtime', timezone.localtime)

    def make_aware(value):
        if getattr(settings, 'USE_TZ', False):
            # naive datetimes are assumed to be in UTC.
            if timezone.is_naive(value):
                value = timezone.make_aware(value, timezone.utc)
            # then convert to the Django configured timezone.
            default_tz = timezone.get_default_timezone()
            value = timezone.localtime(value, default_tz)
        return value

    def make_naive(value):
        if getattr(settings, 'USE_TZ', False):
            default_tz = timezone.get_default_timezone()
            value = timezone.make_naive(value, default_tz)
        return value

    def now():
        if getattr(settings, 'USE_TZ', False):
            return now_localtime(timezone.now())
        else:
            return timezone.now()

except ImportError:
    now = datetime.now
    make_aware = make_naive = lambda x: x
    is_aware = lambda x: False


def maybe_make_aware(value):
    if isinstance(value, datetime) and is_aware(value):
        return value
    if value:
        return make_aware(value)
    return value
