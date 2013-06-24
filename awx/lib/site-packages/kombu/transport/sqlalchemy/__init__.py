"""Kombu transport using SQLAlchemy as the message store."""
# SQLAlchemy overrides != False to have special meaning and pep8 complains
# flake8: noqa

from Queue import Empty

from anyjson import loads, dumps
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from kombu.transport import virtual
from kombu.exceptions import StdConnectionError, StdChannelError

from .models import Queue, Message, metadata


VERSION = (1, 1, 0)
__version__ = '.'.join(map(str, VERSION))


class Channel(virtual.Channel):
    _session = None
    _engines = {}   # engine cache

    def _engine_from_config(self):
        conninfo = self.connection.client
        configuration = dict(conninfo.transport_options)
        url = conninfo.hostname
        return create_engine(url, **configuration)

    def _open(self):
        conninfo = self.connection.client
        if conninfo.hostname not in self._engines:
            engine = self._engine_from_config()
            Session = sessionmaker(bind=engine)
            metadata.create_all(engine)
            self._engines[conninfo.hostname] = engine, Session
        return self._engines[conninfo.hostname]

    @property
    def session(self):
        if self._session is None:
            _, Session = self._open()
            self._session = Session()
        return self._session

    def _get_or_create(self, queue):
        obj = self.session.query(Queue) \
            .filter(Queue.name == queue).first()
        if not obj:
            obj = Queue(queue)
            self.session.add(obj)
            try:
                self.session.commit()
            except OperationalError:
                self.session.rollback()
        return obj

    def _new_queue(self, queue, **kwargs):
        self._get_or_create(queue)

    def _put(self, queue, payload, **kwargs):
        obj = self._get_or_create(queue)
        message = Message(dumps(payload), obj)
        self.session.add(message)
        try:
            self.session.commit()
        except OperationalError:
            self.session.rollback()

    def _get(self, queue):
        obj = self._get_or_create(queue)
        if self.session.bind.name == 'sqlite':
            self.session.execute('BEGIN IMMEDIATE TRANSACTION')
        try:
            msg = self.session.query(Message) \
                .with_lockmode('update') \
                .filter(Message.queue_id == obj.id) \
                .filter(Message.visible != False) \
                .order_by(Message.sent_at) \
                .order_by(Message.id) \
                .limit(1) \
                .first()
            if msg:
                msg.visible = False
                return loads(msg.payload)
            raise Empty()
        finally:
            self.session.commit()

    def _query_all(self, queue):
        obj = self._get_or_create(queue)
        return self.session.query(Message) \
            .filter(Message.queue_id == obj.id)

    def _purge(self, queue):
        count = self._query_all(queue).delete(synchronize_session=False)
        try:
            self.session.commit()
        except OperationalError:
            self.session.rollback()
        return count

    def _size(self, queue):
        return self._query_all(queue).count()


class Transport(virtual.Transport):
    Channel = Channel

    default_port = 0
    connection_errors = (StdConnectionError, )
    channel_errors = (StdChannelError, )
    driver_type = 'sql'
    driver_name = 'sqlalchemy'

    def driver_version(self):
        import sqlalchemy
        return sqlalchemy.__version__
