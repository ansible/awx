import collections
import os
import sqlite3
import sys
import unittest

import pytest

import awx
from awx.main.db.profiled_pg.base import RecordedQueryLog


QUERY = {
    'sql': 'SELECT * FROM main_job',
    'time': '.01'
}
EXPLAIN = 'Seq Scan on public.main_job  (cost=0.00..1.18 rows=18 width=86)'


class FakeDatabase():

    def __init__(self):
        self._cursor = unittest.mock.Mock(spec_sec=['execute', 'fetchall'])
        self._cursor.fetchall.return_value = [(EXPLAIN,)]

    def cursor(self):
        return self._cursor

    @property
    def execute_calls(self):
        return self._cursor.execute.call_args_list


# all of these should still be valid operations we should proxy through
# to the underlying deque object
def test_deque_appendleft():
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    log.appendleft(QUERY)
    assert len(log) == 1


def test_deque_count():
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    log.append(QUERY)
    assert log.count('x') == 0
    assert log.count(QUERY) == 1


def test_deque_clear():
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    log.append(QUERY)
    log.clear()
    assert len(log) == 0


@pytest.mark.parametrize('method', ['extend', 'extendleft'])
def test_deque_extend(method):
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    getattr(log, method)([QUERY])
    assert len(log) == 1


@pytest.mark.parametrize('method', ['pop', 'popleft'])
def test_deque_pop(method):
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    log.append(QUERY)
    getattr(log, method)()
    assert len(log) == 0


def test_deque_remove():
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    log.append(QUERY)
    log.remove(QUERY)
    assert len(log) == 0


def test_deque_reverse():
    log = RecordedQueryLog(collections.deque(), FakeDatabase)
    log.append(QUERY)
    log.reverse()
    assert len(log) == 1


def test_sql_not_recorded_by_default():
    db = FakeDatabase()
    log = RecordedQueryLog(collections.deque(maxlen=100), db)
    assert log.maxlen == 100
    assert log.threshold is None
    log.append(QUERY)
    assert len(log) == 1
    assert [x for x in log] == [QUERY]
    assert db.execute_calls == []


def test_sql_below_threshold():
    db = FakeDatabase()
    log = RecordedQueryLog(collections.deque(maxlen=100), db)
    log.threshold = 1
    log.append(QUERY)
    assert len(log) == 1
    assert [x for x in log] == [QUERY]
    assert db.execute_calls == []


def test_sqlite_failure(tmpdir):
    tmpdir = str(tmpdir)
    db = FakeDatabase()
    db._cursor.execute.side_effect = OSError
    log = RecordedQueryLog(collections.deque(maxlen=100), db, dest=tmpdir)
    log.threshold = 0.00000001
    log.append(QUERY)
    assert len(log) == 1
    assert os.listdir(tmpdir) == []


def test_sql_above_threshold(tmpdir):
    tmpdir = str(tmpdir)
    db = FakeDatabase()
    log = RecordedQueryLog(collections.deque(maxlen=100), db, dest=tmpdir)
    log.threshold = 0.00000001

    for _ in range(5):
        log.append(QUERY)

    assert len(log) == 5
    assert len(db.execute_calls) == 5
    for _call in db.execute_calls:
        args, kw = _call
        assert args == ('EXPLAIN VERBOSE {}'.format(QUERY['sql']),)

    path = os.path.join(
        tmpdir,
        '{}.sqlite'.format(os.path.basename(sys.argv[0]))
    )
    assert os.path.exists(path)

    # verify the results
    def dict_factory(cursor, row):
        d = {}
        for idx,col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    cursor = sqlite3.connect(path)
    cursor.row_factory = dict_factory
    queries_logged = cursor.execute('SELECT * FROM queries').fetchall()
    assert len(queries_logged) == 5
    for q in queries_logged:
        assert q['pid'] == os.getpid()
        assert q['version'] == awx.__version__
        assert q['time'] == 0.01
        assert q['sql'] == QUERY['sql']
        assert EXPLAIN in q['explain']
        assert 'test_sql_above_threshold' in q['bt']
