import psycopg
import select

from contextlib import contextmanager

from awx.settings.application_name import get_application_name

from django.conf import settings
from django.db import connection as pg_connection

NOT_READY = ([], [], [])


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

    @staticmethod
    def current_notifies(conn):
        """
        Altered version of .notifies method from psycopg library
        This removes the outer while True loop so that we only process
        queued notifications
        """
        with conn.lock:
            try:
                ns = conn.wait(psycopg.generators.notifies(conn.pgconn))
            except psycopg.errors._NO_TRACEBACK as ex:
                raise ex.with_traceback(None)
        enc = psycopg._encodings.pgconn_encoding(conn.pgconn)
        for pgn in ns:
            n = psycopg.connection.Notify(pgn.relname.decode(enc), pgn.extra.decode(enc), pgn.be_pid)
            yield n

    def events(self, select_timeout=5, yield_timeouts=False):
        if not self.conn.autocommit:
            raise RuntimeError('Listening for events can only be done in autocommit mode')

        while True:
            if select.select([self.conn], [], [], select_timeout) == NOT_READY:
                if yield_timeouts:
                    yield None
            else:
                notification_generator = self.current_notifies(self.conn)
                for notification in notification_generator:
                    yield notification

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
        conf = settings.DATABASES['default'].copy()
        conf['OPTIONS'] = conf.get('OPTIONS', {}).copy()
        # Modify the application name to distinguish from other connections the process might use
        conf['OPTIONS']['application_name'] = get_application_name(settings.CLUSTER_HOST_ID, function='listener')
        connection_data = f"dbname={conf['NAME']} host={conf['HOST']} user={conf['USER']} password={conf['PASSWORD']} port={conf['PORT']}"
        conn = psycopg.connect(connection_data, autocommit=True, **conf['OPTIONS'])
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
