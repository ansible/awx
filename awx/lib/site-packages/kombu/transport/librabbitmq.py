"""
kombu.transport.librabbitmq
===========================

`librabbitmq`_ transport.

.. _`librabbitmq`: http://pypi.python.org/librabbitmq/

"""
from __future__ import absolute_import

import socket

try:
    import librabbitmq as amqp
    from librabbitmq import ChannelError, ConnectionError
except ImportError:
    try:
        import pylibrabbitmq as amqp                             # noqa
        from pylibrabbitmq import ChannelError, ConnectionError  # noqa
    except ImportError:
        raise ImportError("No module named librabbitmq")

from kombu.exceptions import StdConnectionError, StdChannelError
from kombu.utils.amq_manager import get_manager

from . import base

DEFAULT_PORT = 5672


class Message(base.Message):

    def __init__(self, channel, props, info, body):
        super(Message, self).__init__(
            channel,
            body=body,
            delivery_info=info,
            properties=props,
            delivery_tag=info.get('delivery_tag'),
            content_type=props.get('content_type'),
            content_encoding=props.get('content_encoding'),
            headers=props.get('headers'))


class Channel(amqp.Channel, base.StdChannel):
    Message = Message

    def prepare_message(self, body, priority=None,
                        content_type=None, content_encoding=None,
                        headers=None, properties=None):
        """Encapsulate data into a AMQP message."""
        properties = properties if properties is not None else {}
        properties.update({'content_type': content_type,
                           'content_encoding': content_encoding,
                           'headers': headers,
                           'priority': priority})
        return body, properties


class Connection(amqp.Connection):
    Channel = Channel
    Message = Message


class Transport(base.Transport):
    Connection = Connection

    default_port = DEFAULT_PORT
    connection_errors = (StdConnectionError,
                         ConnectionError,
                         socket.error,
                         IOError,
                         OSError)
    channel_errors = (StdChannelError, ChannelError, )
    driver_type = 'amqp'
    driver_name = 'librabbitmq'

    supports_ev = True
    nb_keep_draining = True

    def __init__(self, client, **kwargs):
        self.client = client
        self.default_port = kwargs.get('default_port') or self.default_port

    def driver_version(self):
        return amqp.__version__

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
        conn = self.Connection(host=conninfo.host,
                               userid=conninfo.userid,
                               password=conninfo.password,
                               virtual_host=conninfo.virtual_host,
                               login_method=conninfo.login_method,
                               insist=conninfo.insist,
                               ssl=conninfo.ssl,
                               connect_timeout=conninfo.connect_timeout)
        conn.client = self.client
        self.client.drain_events = conn.drain_events
        return conn

    def close_connection(self, connection):
        """Close the AMQP broker connection."""
        connection.close()

    def verify_connection(self, connection):
        return connection.connected

    def on_poll_init(self, poller):
        pass

    def on_poll_start(self):
        return {}

    def eventmap(self, connection):
        return {connection.fileno(): self.client.drain_nowait}

    def get_manager(self, *args, **kwargs):
        return get_manager(self.client, *args, **kwargs)

    @property
    def default_connection_params(self):
        return {'userid': 'guest', 'password': 'guest',
                'port': self.default_port,
                'hostname': 'localhost', 'login_method': 'AMQPLAIN'}
