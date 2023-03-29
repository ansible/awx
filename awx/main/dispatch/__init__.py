import os
import psycopg2
import select

from contextlib import contextmanager

from django.conf import settings
from django.db import connection as pg_connection

NOT_READY = ([], [], [])


def get_local_queuename():
    return settings.CLUSTER_HOST_ID


def get_task_queuename():
    if os.getenv('AWX_COMPONENT') != 'web':
        return settings.CLUSTER_HOST_ID

    from awx.main.models.ha import Instance

    random_task_instance = (
        Instance.objects.filter(
            node_type__in=(Instance.Types.CONTROL, Instance.Types.HYBRID),
            node_state=Instance.States.READY,
            enabled=True,
        )
        .only('hostname')
        .order_by('?')
        .first()
    )

    if random_task_instance is None:
        raise ValueError('No task instances are READY and Enabled.')

    return random_task_instance.hostname


class PubSub(object):
    def __init__(self, conn):
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
        if not self.conn.autocommit:
            raise RuntimeError('Listening for events can only be done in autocommit mode')

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
def pg_bus_conn(new_connection=False):
    '''
    Any listeners probably want to establish a new database connection,
    separate from the Django connection used for queries, because that will prevent
    losing connection to the channel whenever a .close() happens.

    Any publishers probably want to use the existing connection
    so that messages follow postgres transaction rules
    https://www.postgresql.org/docs/current/sql-notify.html
    '''

    if new_connection:
        conf = settings.DATABASES['default']
        conn = psycopg2.connect(
            dbname=conf['NAME'], host=conf['HOST'], user=conf['USER'], password=conf['PASSWORD'], port=conf['PORT'], **conf.get("OPTIONS", {})
        )
        # Django connection.cursor().connection doesn't have autocommit=True on by default
        conn.set_session(autocommit=True)
    else:
        if pg_connection.connection is None:
            pg_connection.connect()
        if pg_connection.connection is None:
            raise RuntimeError('Unexpectedly could not connect to postgres for pg_notify actions')
        conn = pg_connection.connection

    pubsub = PubSub(conn)
    yield pubsub
    if new_connection:
        conn.close()
