"""
kombu.transport.pyamqp
======================

pure python amqp transport.

"""
from __future__ import absolute_import

import amqp

from kombu.exceptions import (
    StdConnectionError,
    StdChannelError,
    VersionMismatch,
)
from kombu.utils.amq_manager import get_manager

from . import base

DEFAULT_PORT = 5672

if amqp.VERSION < (0, 9, 3):  # pragma: no cover
    raise VersionMismatch('Please install amqp version 0.9.3 or higher.')


class Message(base.Message):

    def __init__(self, channel, msg, **kwargs):
        props = msg.properties
        super(Message, self).__init__(
            channel,
            body=msg.body,
            delivery_tag=msg.delivery_tag,
            content_type=props.get('content_type'),
            content_encoding=props.get('content_encoding'),
            delivery_info=msg.delivery_info,
            properties=msg.properties,
            headers=props.get('application_headers') or {},
            **kwargs)


class Channel(amqp.Channel, base.StdChannel):
    Message = Message

    def prepare_message(self, body, priority=None,
                        content_type=None, content_encoding=None,
                        headers=None, properties=None):
        """Encapsulate data into a AMQP message."""
        return amqp.Message(body, priority=priority,
                            content_type=content_type,
                            content_encoding=content_encoding,
                            application_headers=headers,
                            **properties)

    def message_to_python(self, raw_message):
        """Convert encoded message body back to a Python value."""
        return self.Message(self, raw_message)


class Connection(amqp.Connection):
    Channel = Channel


class Transport(base.Transport):
    Connection = Connection

    default_port = DEFAULT_PORT

    # it's very annoying that pyamqp sometimes raises AttributeError
    # if the connection is lost, but nothing we can do about that here.
    connection_errors = (
        (StdConnectionError, ) + amqp.Connection.connection_errors
    )
    channel_errors = (StdChannelError, ) + amqp.Connection.channel_errors

    nb_keep_draining = True
    driver_name = "py-amqp"
    driver_type = "amqp"
    supports_heartbeats = True
    supports_ev = True

    def __init__(self, client, **kwargs):
        self.client = client
        self.default_port = kwargs.get("default_port") or self.default_port

    def create_channel(self, connection):
        return connection.channel()

    def drain_events(self, connection, **kwargs):
        return connection.drain_events(**kwargs)

    def establish_connection(self):
        """Establish connection to the AMQP broker."""
        conninfo = self.client
        for name, default_value in self.default_connection_params.items():
            if not getattr(conninfo, name, None):
                setattr(conninfo, name, default_value)
        if conninfo.hostname == 'localhost':
            conninfo.hostname = '127.0.0.1'
        conn = self.Connection(host=conninfo.host,
                               userid=conninfo.userid,
                               password=conninfo.password,
                               login_method=conninfo.login_method,
                               virtual_host=conninfo.virtual_host,
                               insist=conninfo.insist,
                               ssl=conninfo.ssl,
                               connect_timeout=conninfo.connect_timeout,
                               heartbeat=conninfo.heartbeat)
        conn.client = self.client
        return conn

    def close_connection(self, connection):
        """Close the AMQP broker connection."""
        connection.client = None
        connection.close()

    def eventmap(self, connection):
        return {connection.sock: self.client.drain_nowait}

    def on_poll_init(self, poller):
        pass

    def on_poll_start(self):
        return {}

    def heartbeat_check(self, connection, rate=2):
        return connection.heartbeat_tick(rate=rate)

    @property
    def default_connection_params(self):
        return {'userid': 'guest', 'password': 'guest',
                'port': self.default_port,
                'hostname': 'localhost', 'login_method': 'AMQPLAIN'}

    def get_manager(self, *args, **kwargs):
        return get_manager(self.client, *args, **kwargs)
