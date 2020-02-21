import psycopg2
import select
import sys
import logging

from contextlib import contextmanager

from django.conf import settings


NOT_READY = ([], [], [])
if 'run_callback_receiver' in sys.argv:
    logger = logging.getLogger('awx.main.commands.run_callback_receiver')
else:
    logger = logging.getLogger('awx.main.dispatch')


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

    def get_event(self, select_timeout=0):
        # poll the connection, then return one event, if we have one.  Else
        # return None.
        select.select([self.conn], [], [], select_timeout)
        self.conn.poll()
        if self.conn.notifies:
            return self.conn.notifies.pop(0)

    def get_events(self, select_timeout=0):
        # Poll the connection and return all events, if there are any.  Else
        # return None.
        select.select([self.conn], [], [], select_timeout) # redundant?
        self.conn.poll()
        events = []
        while self.conn.notifies:
            events.append(self.conn.notifies.pop(0))
        if events:
            return events

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
                            password=conf['PASSWORD'])
    # Django connection.cursor().connection doesn't have autocommit=True on
    conn.set_session(autocommit=True)
    pubsub = PubSub(conn)
    yield pubsub
    conn.close()


