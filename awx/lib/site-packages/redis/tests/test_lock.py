from __future__ import with_statement
import pytest
import time

from redis.exceptions import LockError, ResponseError
from redis.lock import Lock, LuaLock


class TestLock(object):
    lock_class = Lock

    def get_lock(self, redis, *args, **kwargs):
        kwargs['lock_class'] = self.lock_class
        return redis.lock(*args, **kwargs)

    def test_lock(self, sr):
        lock = self.get_lock(sr, 'foo')
        assert lock.acquire(blocking=False)
        assert sr.get('foo') == lock.local.token
        assert sr.ttl('foo') == -1
        lock.release()
        assert sr.get('foo') is None

    def test_competing_locks(self, sr):
        lock1 = self.get_lock(sr, 'foo')
        lock2 = self.get_lock(sr, 'foo')
        assert lock1.acquire(blocking=False)
        assert not lock2.acquire(blocking=False)
        lock1.release()
        assert lock2.acquire(blocking=False)
        assert not lock1.acquire(blocking=False)
        lock2.release()

    def test_timeout(self, sr):
        lock = self.get_lock(sr, 'foo', timeout=10)
        assert lock.acquire(blocking=False)
        assert 8 < sr.ttl('foo') <= 10
        lock.release()

    def test_float_timeout(self, sr):
        lock = self.get_lock(sr, 'foo', timeout=9.5)
        assert lock.acquire(blocking=False)
        assert 8 < sr.pttl('foo') <= 9500
        lock.release()

    def test_blocking_timeout(self, sr):
        lock1 = self.get_lock(sr, 'foo')
        assert lock1.acquire(blocking=False)
        lock2 = self.get_lock(sr, 'foo', blocking_timeout=0.2)
        start = time.time()
        assert not lock2.acquire()
        assert (time.time() - start) > 0.2
        lock1.release()

    def test_context_manager(self, sr):
        # blocking_timeout prevents a deadlock if the lock can't be acquired
        # for some reason
        with self.get_lock(sr, 'foo', blocking_timeout=0.2) as lock:
            assert sr.get('foo') == lock.local.token
        assert sr.get('foo') is None

    def test_high_sleep_raises_error(self, sr):
        "If sleep is higher than timeout, it should raise an error"
        with pytest.raises(LockError):
            self.get_lock(sr, 'foo', timeout=1, sleep=2)

    def test_releasing_unlocked_lock_raises_error(self, sr):
        lock = self.get_lock(sr, 'foo')
        with pytest.raises(LockError):
            lock.release()

    def test_releasing_lock_no_longer_owned_raises_error(self, sr):
        lock = self.get_lock(sr, 'foo')
        lock.acquire(blocking=False)
        # manually change the token
        sr.set('foo', 'a')
        with pytest.raises(LockError):
            lock.release()
        # even though we errored, the token is still cleared
        assert lock.local.token is None

    def test_extend_lock(self, sr):
        lock = self.get_lock(sr, 'foo', timeout=10)
        assert lock.acquire(blocking=False)
        assert 8000 < sr.pttl('foo') <= 10000
        assert lock.extend(10)
        assert 16000 < sr.pttl('foo') <= 20000
        lock.release()

    def test_extend_lock_float(self, sr):
        lock = self.get_lock(sr, 'foo', timeout=10.0)
        assert lock.acquire(blocking=False)
        assert 8000 < sr.pttl('foo') <= 10000
        assert lock.extend(10.0)
        assert 16000 < sr.pttl('foo') <= 20000
        lock.release()

    def test_extending_unlocked_lock_raises_error(self, sr):
        lock = self.get_lock(sr, 'foo', timeout=10)
        with pytest.raises(LockError):
            lock.extend(10)

    def test_extending_lock_with_no_timeout_raises_error(self, sr):
        lock = self.get_lock(sr, 'foo')
        assert lock.acquire(blocking=False)
        with pytest.raises(LockError):
            lock.extend(10)
        lock.release()

    def test_extending_lock_no_longer_owned_raises_error(self, sr):
        lock = self.get_lock(sr, 'foo')
        assert lock.acquire(blocking=False)
        sr.set('foo', 'a')
        with pytest.raises(LockError):
            lock.extend(10)


class TestLuaLock(TestLock):
    lock_class = LuaLock


class TestLockClassSelection(object):
    def test_lock_class_argument(self, sr):
        lock = sr.lock('foo', lock_class=Lock)
        assert type(lock) == Lock
        lock = sr.lock('foo', lock_class=LuaLock)
        assert type(lock) == LuaLock

    def test_cached_lualock_flag(self, sr):
        try:
            sr._use_lua_lock = True
            lock = sr.lock('foo')
            assert type(lock) == LuaLock
        finally:
            sr._use_lua_lock = None

    def test_cached_lock_flag(self, sr):
        try:
            sr._use_lua_lock = False
            lock = sr.lock('foo')
            assert type(lock) == Lock
        finally:
            sr._use_lua_lock = None

    def test_lua_compatible_server(self, sr, monkeypatch):
        @classmethod
        def mock_register(cls, redis):
            return
        monkeypatch.setattr(LuaLock, 'register_scripts', mock_register)
        try:
            lock = sr.lock('foo')
            assert type(lock) == LuaLock
            assert sr._use_lua_lock is True
        finally:
            sr._use_lua_lock = None

    def test_lua_unavailable(self, sr, monkeypatch):
        @classmethod
        def mock_register(cls, redis):
            raise ResponseError()
        monkeypatch.setattr(LuaLock, 'register_scripts', mock_register)
        try:
            lock = sr.lock('foo')
            assert type(lock) == Lock
            assert sr._use_lua_lock is False
        finally:
            sr._use_lua_lock = None
