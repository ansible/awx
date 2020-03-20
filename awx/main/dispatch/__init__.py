import psycopg2
import select

from contextlib import contextmanager

from django.conf import settings


NOT_READY = ([], [], [])


def get_local_queuename():
    return settings.CLUSTER_HOST_ID


class PubSub(object):
    def __init__(self, conn):
        assert conn.autocommit, "Connection must be in autocommit mode."
        self.conn = conn

    def listen(self, channel):
        with self.conn.cursor() as cur:
            cur.execute('LISTEN "%s";' % channel)

    def unlisten(self, channel):
        with self.conn.cursor() as cur:
            cur.execute('UNLISTEN "%s";' % channel)

    def notify(self, channel, payload):
        with self.conn.cursor() as cur:
            cur.execute('SELECT pg_notify(%s, %s);', (channel, payload))

    def events(self, select_timeout=5, yield_timeouts=False):
        while True:
            if select.select([self.conn], [], [], select_timeout) == NOT_READY:
                if yield_timeouts:
                    yield None
            else:
                self.conn.poll()
                while self.conn.notifies:
                    yield self.conn.notifies.pop(0)

    def close(self):
        self.conn.close()


@contextmanager
def pg_bus_conn():
    conf = settings.DATABASES['default']
    conn = psycopg2.connect(dbname=conf['NAME'],
                            host=conf['HOST'],
                            user=conf['USER'],
                            password=conf['PASSWORD'],
                            port=conf['PORT'],
                            **conf.get("OPTIONS", {}))
    # Django connection.cursor().connection doesn't have autocommit=True on
    conn.set_session(autocommit=True)
    pubsub = PubSub(conn)
    yield pubsub
    conn.close()


