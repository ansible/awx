from __future__ import with_statement
import os
import pytest
import redis
import time
import re

from threading import Thread
from redis.connection import ssl_available
from .conftest import skip_if_server_version_lt


class DummyConnection(object):
    description_format = "DummyConnection<>"

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.pid = os.getpid()


class TestConnectionPool(object):
    def get_pool(self, connection_kwargs=None, max_connections=None,
                 connection_class=DummyConnection):
        connection_kwargs = connection_kwargs or {}
        pool = redis.ConnectionPool(
            connection_class=connection_class,
            max_connections=max_connections,
            **connection_kwargs)
        return pool

    def test_connection_creation(self):
        connection_kwargs = {'foo': 'bar', 'biz': 'baz'}
        pool = self.get_pool(connection_kwargs=connection_kwargs)
        connection = pool.get_connection('_')
        assert isinstance(connection, DummyConnection)
        assert connection.kwargs == connection_kwargs

    def test_multiple_connections(self):
        pool = self.get_pool()
        c1 = pool.get_connection('_')
        c2 = pool.get_connection('_')
        assert c1 != c2

    def test_max_connections(self):
        pool = self.get_pool(max_connections=2)
        pool.get_connection('_')
        pool.get_connection('_')
        with pytest.raises(redis.ConnectionError):
            pool.get_connection('_')

    def test_reuse_previously_released_connection(self):
        pool = self.get_pool()
        c1 = pool.get_connection('_')
        pool.release(c1)
        c2 = pool.get_connection('_')
        assert c1 == c2

    def test_repr_contains_db_info_tcp(self):
        connection_kwargs = {'host': 'localhost', 'port': 6379, 'db': 1}
        pool = self.get_pool(connection_kwargs=connection_kwargs,
                             connection_class=redis.Connection)
        expected = 'ConnectionPool<Connection<host=localhost,port=6379,db=1>>'
        assert repr(pool) == expected

    def test_repr_contains_db_info_unix(self):
        connection_kwargs = {'path': '/abc', 'db': 1}
        pool = self.get_pool(connection_kwargs=connection_kwargs,
                             connection_class=redis.UnixDomainSocketConnection)
        expected = 'ConnectionPool<UnixDomainSocketConnection<path=/abc,db=1>>'
        assert repr(pool) == expected


class TestBlockingConnectionPool(object):
    def get_pool(self, connection_kwargs=None, max_connections=10, timeout=20):
        connection_kwargs = connection_kwargs or {}
        pool = redis.BlockingConnectionPool(connection_class=DummyConnection,
                                            max_connections=max_connections,
                                            timeout=timeout,
                                            **connection_kwargs)
        return pool

    def test_connection_creation(self):
        connection_kwargs = {'foo': 'bar', 'biz': 'baz'}
        pool = self.get_pool(connection_kwargs=connection_kwargs)
        connection = pool.get_connection('_')
        assert isinstance(connection, DummyConnection)
        assert connection.kwargs == connection_kwargs

    def test_multiple_connections(self):
        pool = self.get_pool()
        c1 = pool.get_connection('_')
        c2 = pool.get_connection('_')
        assert c1 != c2

    def test_connection_pool_blocks_until_timeout(self):
        "When out of connections, block for timeout seconds, then raise"
        pool = self.get_pool(max_connections=1, timeout=0.1)
        pool.get_connection('_')

        start = time.time()
        with pytest.raises(redis.ConnectionError):
            pool.get_connection('_')
        # we should have waited at least 0.1 seconds
        assert time.time() - start >= 0.1

    def connection_pool_blocks_until_another_connection_released(self):
        """
        When out of connections, block until another connection is released
        to the pool
        """
        pool = self.get_pool(max_connections=1, timeout=2)
        c1 = pool.get_connection('_')

        def target():
            time.sleep(0.1)
            pool.release(c1)

        Thread(target=target).start()
        start = time.time()
        pool.get_connection('_')
        assert time.time() - start >= 0.1

    def test_reuse_previously_released_connection(self):
        pool = self.get_pool()
        c1 = pool.get_connection('_')
        pool.release(c1)
        c2 = pool.get_connection('_')
        assert c1 == c2

    def test_repr_contains_db_info_tcp(self):
        pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        expected = 'ConnectionPool<Connection<host=localhost,port=6379,db=0>>'
        assert repr(pool) == expected

    def test_repr_contains_db_info_unix(self):
        pool = redis.ConnectionPool(
            connection_class=redis.UnixDomainSocketConnection,
            path='abc',
            db=0,
        )
        expected = 'ConnectionPool<UnixDomainSocketConnection<path=abc,db=0>>'
        assert repr(pool) == expected


class TestConnectionPoolURLParsing(object):
    def test_defaults(self):
        pool = redis.ConnectionPool.from_url('redis://localhost')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    def test_hostname(self):
        pool = redis.ConnectionPool.from_url('redis://myhost')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'myhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    def test_port(self):
        pool = redis.ConnectionPool.from_url('redis://localhost:6380')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6380,
            'db': 0,
            'password': None,
        }

    def test_password(self):
        pool = redis.ConnectionPool.from_url('redis://:mypassword@localhost')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': 'mypassword',
        }

    def test_db_as_argument(self):
        pool = redis.ConnectionPool.from_url('redis://localhost', db='1')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 1,
            'password': None,
        }

    def test_db_in_path(self):
        pool = redis.ConnectionPool.from_url('redis://localhost/2', db='1')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 2,
            'password': None,
        }

    def test_db_in_querystring(self):
        pool = redis.ConnectionPool.from_url('redis://localhost/2?db=3',
                                             db='1')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 3,
            'password': None,
        }

    def test_extra_querystring_options(self):
        pool = redis.ConnectionPool.from_url('redis://localhost?a=1&b=2')
        assert pool.connection_class == redis.Connection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
            'a': '1',
            'b': '2'
        }

    def test_calling_from_subclass_returns_correct_instance(self):
        pool = redis.BlockingConnectionPool.from_url('redis://localhost')
        assert isinstance(pool, redis.BlockingConnectionPool)

    def test_client_creates_connection_pool(self):
        r = redis.StrictRedis.from_url('redis://myhost')
        assert r.connection_pool.connection_class == redis.Connection
        assert r.connection_pool.connection_kwargs == {
            'host': 'myhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }


class TestConnectionPoolUnixSocketURLParsing(object):
    def test_defaults(self):
        pool = redis.ConnectionPool.from_url('unix:///socket')
        assert pool.connection_class == redis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': None,
        }

    def test_password(self):
        pool = redis.ConnectionPool.from_url('unix://:mypassword@/socket')
        assert pool.connection_class == redis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': 'mypassword',
        }

    def test_db_as_argument(self):
        pool = redis.ConnectionPool.from_url('unix:///socket', db=1)
        assert pool.connection_class == redis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 1,
            'password': None,
        }

    def test_db_in_querystring(self):
        pool = redis.ConnectionPool.from_url('unix:///socket?db=2', db=1)
        assert pool.connection_class == redis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 2,
            'password': None,
        }

    def test_extra_querystring_options(self):
        pool = redis.ConnectionPool.from_url('unix:///socket?a=1&b=2')
        assert pool.connection_class == redis.UnixDomainSocketConnection
        assert pool.connection_kwargs == {
            'path': '/socket',
            'db': 0,
            'password': None,
            'a': '1',
            'b': '2'
        }


class TestSSLConnectionURLParsing(object):
    @pytest.mark.skipif(not ssl_available, reason="SSL not installed")
    def test_defaults(self):
        pool = redis.ConnectionPool.from_url('rediss://localhost')
        assert pool.connection_class == redis.SSLConnection
        assert pool.connection_kwargs == {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
        }

    @pytest.mark.skipif(not ssl_available, reason="SSL not installed")
    def test_cert_reqs_options(self):
        import ssl
        pool = redis.ConnectionPool.from_url('rediss://?ssl_cert_reqs=none')
        assert pool.get_connection('_').cert_reqs == ssl.CERT_NONE

        pool = redis.ConnectionPool.from_url(
            'rediss://?ssl_cert_reqs=optional')
        assert pool.get_connection('_').cert_reqs == ssl.CERT_OPTIONAL

        pool = redis.ConnectionPool.from_url(
            'rediss://?ssl_cert_reqs=required')
        assert pool.get_connection('_').cert_reqs == ssl.CERT_REQUIRED


class TestConnection(object):
    def test_on_connect_error(self):
        """
        An error in Connection.on_connect should disconnect from the server
        see for details: https://github.com/andymccurdy/redis-py/issues/368
        """
        # this assumes the Redis server being tested against doesn't have
        # 9999 databases ;)
        bad_connection = redis.Redis(db=9999)
        # an error should be raised on connect
        with pytest.raises(redis.RedisError):
            bad_connection.info()
        pool = bad_connection.connection_pool
        assert len(pool._available_connections) == 1
        assert not pool._available_connections[0]._sock

    @skip_if_server_version_lt('2.8.8')
    def test_busy_loading_disconnects_socket(self, r):
        """
        If Redis raises a LOADING error, the connection should be
        disconnected and a BusyLoadingError raised
        """
        with pytest.raises(redis.BusyLoadingError):
            r.execute_command('DEBUG', 'ERROR', 'LOADING fake message')
        pool = r.connection_pool
        assert len(pool._available_connections) == 1
        assert not pool._available_connections[0]._sock

    @skip_if_server_version_lt('2.8.8')
    def test_busy_loading_from_pipeline_immediate_command(self, r):
        """
        BusyLoadingErrors should raise from Pipelines that execute a
        command immediately, like WATCH does.
        """
        pipe = r.pipeline()
        with pytest.raises(redis.BusyLoadingError):
            pipe.immediate_execute_command('DEBUG', 'ERROR',
                                           'LOADING fake message')
        pool = r.connection_pool
        assert not pipe.connection
        assert len(pool._available_connections) == 1
        assert not pool._available_connections[0]._sock

    @skip_if_server_version_lt('2.8.8')
    def test_busy_loading_from_pipeline(self, r):
        """
        BusyLoadingErrors should be raised from a pipeline execution
        regardless of the raise_on_error flag.
        """
        pipe = r.pipeline()
        pipe.execute_command('DEBUG', 'ERROR', 'LOADING fake message')
        with pytest.raises(redis.BusyLoadingError):
            pipe.execute()
        pool = r.connection_pool
        assert not pipe.connection
        assert len(pool._available_connections) == 1
        assert not pool._available_connections[0]._sock

    @skip_if_server_version_lt('2.8.8')
    def test_read_only_error(self, r):
        "READONLY errors get turned in ReadOnlyError exceptions"
        with pytest.raises(redis.ReadOnlyError):
            r.execute_command('DEBUG', 'ERROR', 'READONLY blah blah')

    def test_connect_from_url_tcp(self):
        connection = redis.Redis.from_url('redis://localhost')
        pool = connection.connection_pool

        assert re.match('(.*)<(.*)<(.*)>>', repr(pool)).groups() == (
            'ConnectionPool',
            'Connection',
            'host=localhost,port=6379,db=0',
        )

    def test_connect_from_url_unix(self):
        connection = redis.Redis.from_url('unix:///path/to/socket')
        pool = connection.connection_pool

        assert re.match('(.*)<(.*)<(.*)>>', repr(pool)).groups() == (
            'ConnectionPool',
            'UnixDomainSocketConnection',
            'path=/path/to/socket,db=0',
        )
