import gevent
import weakref

try:
    import redis
except ImportError:
    pass


class RedisStorage(object):
    def __init__(self, server, **kwargs):
        self.server = weakref.proxy(server)
        self.jobs = []
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 6379)
        r = redis.StrictRedis(host=self.host, port=self.port)
        self.conn = r.pubsub()
        self.spawn(self.listener)

    def listener(self):
        for m in self.conn.listen():
            print("===============NEW MESSAGE!!!====== %s", m)

    def spawn(self, fn, *args, **kwargs):
        new = gevent.spawn(fn, *args, **kwargs)
        self.jobs.append(new)
        return new

    def new_request(self, environ):
        print("===========NEW REQUEST %s===========" % environ)
