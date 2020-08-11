import os
import pkg_resources
import sqlite3
import sys
import traceback
import uuid

from django.core.cache import cache
from django.core.cache.backends.locmem import LocMemCache
from django.db.backends.postgresql.base import DatabaseWrapper as BaseDatabaseWrapper

from awx.main.utils import memoize

__loc__ = LocMemCache(str(uuid.uuid4()), {})
__all__ = ['DatabaseWrapper']


class RecordedQueryLog(object):

    def __init__(self, log, db, dest='/var/log/tower/profile'):
        self.log = log
        self.db = db
        self.dest = dest
        try:
            self.threshold = cache.get('awx-profile-sql-threshold')
        except Exception:
            # if we can't reach the cache, just assume profiling's off
            self.threshold = None

    def append(self, query):
        ret = self.log.append(query)
        try:
            self.write(query)
        except Exception:
            # not sure what else to do her e- we can't really safely
            # *use* our loggers because it'll just generate more DB queries
            # and potentially recurse into this state again
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb)
        return ret

    def write(self, query):
        if self.threshold is None:
            return
        seconds = float(query['time'])

        # if the query is slow enough...
        if seconds >= self.threshold:
            sql = query['sql']
            if sql.startswith('EXPLAIN'):
                return

            # build a printable Python stack
            bt = ' '.join(traceback.format_stack())

            # and re-run the same query w/ EXPLAIN
            explain = ''
            cursor = self.db.cursor()
            cursor.execute('EXPLAIN VERBOSE {}'.format(sql))
            for line in cursor.fetchall():
                explain += line[0] + '\n'

            # write a row of data into a per-PID sqlite database
            if not os.path.isdir(self.dest):
                os.makedirs(self.dest)
            progname = ' '.join(sys.argv)
            for match in ('uwsgi', 'dispatcher', 'callback_receiver', 'wsbroadcast'):
                if match in progname:
                    progname = match
                    break
            else:
                progname = os.path.basename(sys.argv[0])
            filepath = os.path.join(
                self.dest,
                '{}.sqlite'.format(progname)
            )
            version = pkg_resources.get_distribution('awx').version
            log = sqlite3.connect(filepath, timeout=3)
            log.execute(
                'CREATE TABLE IF NOT EXISTS queries ('
                '   id INTEGER PRIMARY KEY,'
                '   version TEXT,'
                '   pid INTEGER,'
                '   stamp DATETIME DEFAULT CURRENT_TIMESTAMP,'
                '   argv REAL,'
                '   time REAL,'
                '   sql TEXT,'
                '   explain TEXT,'
                '   bt TEXT'
                ');'
            )
            log.commit()
            log.execute(
                'INSERT INTO queries (pid, version, argv, time, sql, explain, bt) '
                'VALUES (?, ?, ?, ?, ?, ?, ?);',
                (os.getpid(), version, ' ' .join(sys.argv), seconds, sql, explain, bt)
            )
            log.commit()

    def __len__(self):
        return len(self.log)

    def __iter__(self):
        return iter(self.log)

    def __getattr__(self, attr):
        return getattr(self.log, attr)


class DatabaseWrapper(BaseDatabaseWrapper):
    """
    This is a special subclass of Django's postgres DB backend which - based on
    the value of a special flag in cache - captures slow queries and
    writes profile and Python stack metadata to the disk.
    """

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        # Django's default base wrapper implementation has `queries_log`
        # which is a `collections.deque` that every query is appended to
        #
        # this line wraps the deque with a proxy that can capture each query
        # and - if it's slow enough - record profiling metadata to the file
        # system for debugging purposes
        self.queries_log = RecordedQueryLog(self.queries_log, self)

    @property
    @memoize(ttl=1, cache=__loc__)
    def force_debug_cursor(self):
        # in Django's base DB implementation, `self.force_debug_cursor` is just
        # a simple boolean, and this value is used to signal to Django that it
        # should record queries into `self.queries_log` as they're executed (this
        # is the same mechanism used by libraries like the django-debug-toolbar)
        #
        # in _this_ implementation, we represent it as a property which will
        # check the cache for a special flag to be set (when the flag is set, it
        # means we should start recording queries because somebody called
        # `awx-manage profile_sql`)
        #
        # it's worth noting that this property is wrapped w/ @memoize because
        # Django references this attribute _constantly_ (in particular, once
        # per executed query); doing a cache.get()  _at most_ once per
        # second is a good enough window to detect when profiling is turned
        # on/off by a system administrator
        try:
            threshold = cache.get('awx-profile-sql-threshold')
        except Exception:
            # if we can't reach the cache, just assume profiling's off
            threshold = None
        self.queries_log.threshold = threshold
        return threshold is not None

    @force_debug_cursor.setter
    def force_debug_cursor(self, v):
        return
