"""
Redis Backends
------------------

Provides backends for talking to `Redis <http://redis.io>`_.

"""

from __future__ import absolute_import
from dogpile.cache.api import CacheBackend, NO_VALUE
from dogpile.cache.compat import pickle, u

redis = None

__all__ = 'RedisBackend',


class RedisBackend(CacheBackend):
    """A `Redis <http://redis.io/>`_ backend, using the
    `redis-py <http://pypi.python.org/pypi/redis/>`_ backend.

    Example configuration::

        from dogpile.cache import make_region

        region = make_region().configure(
            'dogpile.cache.redis',
            arguments = {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'redis_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True
                }
        )

    Arguments accepted in the arguments dictionary:

    :param url: string. If provided, will override separate host/port/db
     params.  The format is that accepted by ``StrictRedis.from_url()``.

     .. versionadded:: 0.4.1

    :param host: string, default is ``localhost``.

    :param password: string, default is no password.

     .. versionadded:: 0.4.1

    :param port: integer, default is ``6379``.

    :param db: integer, default is ``0``.

    :param redis_expiration_time: integer, number of seconds after setting
     a value that Redis should expire it.  This should be larger than dogpile's
     cache expiration.  By default no expiration is set.

    :param distributed_lock: boolean, when True, will use a
     redis-lock as the dogpile lock.
     Use this when multiple
     processes will be talking to the same redis instance.
     When left at False, dogpile will coordinate on a regular
     threading mutex.

    :param lock_timeout: integer, number of seconds after acquiring a lock that
     Redis should expire it.  This argument is only valid when
     ``distributed_lock`` is ``True``.

     .. versionadded:: 0.5.0

    :param socket_timeout: float, seconds for socket timeout.
     Default is None (no timeout).

     .. versionadded:: 0.5.4

    :param lock_sleep: integer, number of seconds to sleep when failed to
     acquire a lock.  This argument is only valid when
     ``distributed_lock`` is ``True``.

     .. versionadded:: 0.5.0

    :param connection_pool: ``redis.ConnectionPool`` object.  If provided,
     this object supersedes other connection arguments passed to the
     ``redis.StrictRedis`` instance, including url and/or host as well as
     socket_timeout, and will be passed to ``redis.StrictRedis`` as the
     source of connectivity.

     .. versionadded:: 0.5.4


    """

    def __init__(self, arguments):
        self._imports()
        self.url = arguments.pop('url', None)
        self.host = arguments.pop('host', 'localhost')
        self.password = arguments.pop('password', None)
        self.port = arguments.pop('port', 6379)
        self.db = arguments.pop('db', 0)
        self.distributed_lock = arguments.get('distributed_lock', False)
        self.socket_timeout = arguments.pop('socket_timeout', None)

        self.lock_timeout = arguments.get('lock_timeout', None)
        self.lock_sleep = arguments.get('lock_sleep', 0.1)

        self.redis_expiration_time = arguments.pop('redis_expiration_time', 0)
        self.connection_pool = arguments.get('connection_pool', None)
        self.client = self._create_client()

    def _imports(self):
        # defer imports until backend is used
        global redis
        import redis  # noqa

    def _create_client(self):
        if self.connection_pool is not None:
            # the connection pool already has all other connection
            # options present within, so here we disregard socket_timeout
            # and others.
            return redis.StrictRedis(connection_pool=self.connection_pool)

        args = {}
        if self.socket_timeout:
            args['socket_timeout'] = self.socket_timeout

        if self.url is not None:
            args.update(url=self.url)
            return redis.StrictRedis.from_url(**args)
        else:
            args.update(
                host=self.host, password=self.password,
                port=self.port, db=self.db
            )
            return redis.StrictRedis(**args)

    def get_mutex(self, key):
        if self.distributed_lock:
            return self.client.lock(u('_lock{0}').format(key),
                                    self.lock_timeout, self.lock_sleep)
        else:
            return None

    def get(self, key):
        value = self.client.get(key)
        if value is None:
            return NO_VALUE
        return pickle.loads(value)

    def get_multi(self, keys):
        values = self.client.mget(keys)
        return [
            pickle.loads(v) if v is not None else NO_VALUE
            for v in values]

    def set(self, key, value):
        if self.redis_expiration_time:
            self.client.setex(key, self.redis_expiration_time,
                              pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
        else:
            self.client.set(key, pickle.dumps(value, pickle.HIGHEST_PROTOCOL))

    def set_multi(self, mapping):
        mapping = dict(
            (k, pickle.dumps(v, pickle.HIGHEST_PROTOCOL))
            for k, v in mapping.items()
        )

        if not self.redis_expiration_time:
            self.client.mset(mapping)
        else:
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, self.redis_expiration_time, value)
            pipe.execute()

    def delete(self, key):
        self.client.delete(key)

    def delete_multi(self, keys):
        self.client.delete(*keys)
