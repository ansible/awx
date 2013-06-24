"""
kombu.transport.virtual
=======================

Virtual transport implementation.

Emulates the AMQ API for non-AMQ transports.

"""
from __future__ import absolute_import

import base64
import socket
import warnings

from itertools import count
from time import sleep, time
from Queue import Empty

from kombu.exceptions import StdChannelError
from kombu.utils import emergency_dump_state, say, uuid
from kombu.utils.compat import OrderedDict
from kombu.utils.encoding import str_to_bytes, bytes_to_str
from kombu.utils.finalize import Finalize

from kombu.transport import base

from .scheduling import FairCycle
from .exchange import STANDARD_EXCHANGE_TYPES

UNDELIVERABLE_FMT = """\
Message could not be delivered: No queues bound to exchange %(exchange)r
using binding key %(routing_key)r
"""


class Base64(object):

    def encode(self, s):
        return bytes_to_str(base64.b64encode(str_to_bytes(s)))

    def decode(self, s):
        return base64.b64decode(str_to_bytes(s))


class NotEquivalentError(Exception):
    """Entity declaration is not equivalent to the previous declaration."""
    pass


class UndeliverableWarning(UserWarning):
    """The message could not be delivered to a queue."""
    pass


class BrokerState(object):

    #: exchange declarations.
    exchanges = None

    #: active bindings.
    bindings = None

    def __init__(self, exchanges=None, bindings=None):
        self.exchanges = {} if exchanges is None else exchanges
        self.bindings = {} if bindings is None else bindings

    def clear(self):
        self.exchanges.clear()
        self.bindings.clear()


class QoS(object):
    """Quality of Service guarantees.

    Only supports `prefetch_count` at this point.

    :param channel: AMQ Channel.
    :keyword prefetch_count: Initial prefetch count (defaults to 0).

    """

    #: current prefetch count value
    prefetch_count = 0

    #: :class:`~collections.OrderedDict` of active messages.
    #: *NOTE*: Can only be modified by the consuming thread.
    _delivered = None

    #: acks can be done by other threads than the consuming thread.
    #: Instead of a mutex, which doesn't perform well here, we mark
    #: the delivery tags as dirty, so subsequent calls to append() can remove
    #: them.
    _dirty = None

    #: If disabled, unacked messages won't be restored at shutdown.
    restore_at_shutdown = True

    def __init__(self, channel, prefetch_count=0):
        self.channel = channel
        self.prefetch_count = prefetch_count or 0

        self._delivered = OrderedDict()
        self._delivered.restored = False
        self._dirty = set()
        self._on_collect = Finalize(self,
                                    self.restore_unacked_once,
                                    exitpriority=1)

    def can_consume(self):
        """Returns true if the channel can be consumed from.

        Used to ensure the client adhers to currently active
        prefetch limits.

        """
        pcount = self.prefetch_count
        return not pcount or len(self._delivered) - len(self._dirty) < pcount

    def append(self, message, delivery_tag):
        """Append message to transactional state."""
        if self._dirty:
            self._flush()
        self._delivered[delivery_tag] = message

    def get(self, delivery_tag):
        return self._delivered[delivery_tag]

    def _flush(self):
        """Flush dirty (acked/rejected) tags from."""
        dirty = self._dirty
        delivered = self._delivered
        while 1:
            try:
                dirty_tag = dirty.pop()
            except KeyError:
                break
            delivered.pop(dirty_tag, None)

    def ack(self, delivery_tag):
        """Acknowledge message and remove from transactional state."""
        self._dirty.add(delivery_tag)

    def reject(self, delivery_tag, requeue=False):
        """Remove from transactional state and requeue message."""
        if requeue:
            self.channel._restore(self._delivered[delivery_tag])
        self._dirty.add(delivery_tag)

    def restore_unacked(self):
        """Restore all unacknowledged messages."""
        self._flush()
        delivered = self._delivered
        errors = []

        while delivered:
            try:
                _, message = delivered.popitem()
            except KeyError:  # pragma: no cover
                break

            try:
                self.channel._restore(message)
            except BaseException, exc:
                errors.append((exc, message))
        delivered.clear()
        return errors

    def restore_unacked_once(self):
        """Restores all unacknowledged message at shutdown/gc collect.

        Will only be done once for each instance.

        """
        self._on_collect.cancel()
        self._flush()
        state = self._delivered

        if not self.restore_at_shutdown:
            return
        elif not self.channel.do_restore or getattr(state, 'restored', None):
            assert not state
            return

        try:
            if state:
                say('Restoring %r unacknowledged message(s).',
                    len(self._delivered))
                unrestored = self.restore_unacked()

                if unrestored:
                    errors, messages = zip(*unrestored)
                    say('UNABLE TO RESTORE %s MESSAGES: %s',
                        len(errors), errors)
                    emergency_dump_state(messages)
        finally:
            state.restored = True

    def restore_visible(self, start=0, num=10, interval=10):
        pass


class Message(base.Message):

    def __init__(self, channel, payload, **kwargs):
        self._raw = payload
        properties = payload['properties']
        body = payload.get('body')
        if body:
            body = channel.decode_body(body, properties.get('body_encoding'))
        fields = {'body': body,
                  'delivery_tag': properties['delivery_tag'],
                  'content_type': payload.get('content-type'),
                  'content_encoding': payload.get('content-encoding'),
                  'headers': payload.get('headers'),
                  'properties': properties,
                  'delivery_info': properties.get('delivery_info'),
                  'postencode': 'utf-8'}
        super(Message, self).__init__(channel, **dict(kwargs, **fields))

    def serializable(self):
        props = self.properties
        body, _ = self.channel.encode_body(self.body,
                                           props.get('body_encoding'))
        headers = dict(self.headers)
        # remove compression header
        headers.pop('compression', None)
        return {'body': body,
                'properties': props,
                'content-type': self.content_type,
                'content-encoding': self.content_encoding,
                'headers': headers}


class AbstractChannel(object):
    """This is an abstract class defining the channel methods
    you'd usually want to implement in a virtual channel.

    Do not subclass directly, but rather inherit from :class:`Channel`
    instead.

    """

    def _get(self, queue, timeout=None):
        """Get next message from `queue`."""
        raise NotImplementedError('Virtual channels must implement _get')

    def _put(self, queue, message):
        """Put `message` onto `queue`."""
        raise NotImplementedError('Virtual channels must implement _put')

    def _purge(self, queue):
        """Remove all messages from `queue`."""
        raise NotImplementedError('Virtual channels must implement _purge')

    def _size(self, queue):
        """Return the number of messages in `queue` as an :class:`int`."""
        return 0

    def _delete(self, queue, *args, **kwargs):
        """Delete `queue`.

        This just purges the queue, if you need to do more you can
        override this method.

        """
        self._purge(queue)

    def _new_queue(self, queue, **kwargs):
        """Create new queue.

        Some implementations needs to do additional actions when
        the queue is created.  You can do so by overriding this
        method.

        """
        pass

    def _has_queue(self, queue, **kwargs):
        """Verify that queue exists.

        Should return :const:`True` if the queue exists or :const:`False`
        otherwise.

        """
        return True

    def _poll(self, cycle, timeout=None):
        """Poll a list of queues for available messages."""
        return cycle.get()


class Channel(AbstractChannel, base.StdChannel):
    """Virtual channel.

    :param connection: The transport instance this channel is part of.

    """
    #: message class used.
    Message = Message

    #: QoS class used.
    QoS = QoS

    #: flag to restore unacked messages when channel
    #: goes out of scope.
    do_restore = True

    #: mapping of exchange types and corresponding classes.
    exchange_types = dict(STANDARD_EXCHANGE_TYPES)

    #: flag set if the channel supports fanout exchanges.
    supports_fanout = False

    #: Binary <-> ASCII codecs.
    codecs = {'base64': Base64()}

    #: Default body encoding.
    #: NOTE: ``transport_options['body_encoding']`` will override this value.
    body_encoding = 'base64'

    #: counter used to generate delivery tags for this channel.
    _next_delivery_tag = count(1).next

    #: Optional queue where messages with no route is delivered.
    #: Set by ``transport_options['deadletter_queue']``.
    deadletter_queue = None

    # List of options to transfer from :attr:`transport_options`.
    from_transport_options = ('body_encoding', 'deadletter_queue')

    def __init__(self, connection, **kwargs):
        self.connection = connection
        self._consumers = set()
        self._cycle = None
        self._tag_to_queue = {}
        self._active_queues = []
        self._qos = None
        self.closed = False

        # instantiate exchange types
        self.exchange_types = dict(
            (typ, cls(self)) for typ, cls in self.exchange_types.items()
        )

        self.channel_id = self.connection._next_channel_id()

        topts = self.connection.client.transport_options
        for opt_name in self.from_transport_options:
            try:
                setattr(self, opt_name, topts[opt_name])
            except KeyError:
                pass

    def exchange_declare(self, exchange=None, type='direct', durable=False,
                         auto_delete=False, arguments=None,
                         nowait=False, passive=False):
        """Declare exchange."""
        type = type or 'direct'
        exchange = exchange or 'amq.%s' % (type, )
        if passive:
            if exchange not in self.state.exchanges:
                raise StdChannelError(
                    '404',
                    u'NOT_FOUND - no exchange %r in vhost %r' % (
                        exchange, self.connection.client.virtual_host or '/'),
                    (50, 10), 'Channel.exchange_declare')
            return
        try:
            prev = self.state.exchanges[exchange]
            if not self.typeof(exchange).equivalent(prev, exchange, type,
                                                    durable, auto_delete,
                                                    arguments):
                raise NotEquivalentError(
                    'Cannot redeclare exchange %r in vhost %r with '
                    'different type, durable or autodelete value' % (
                        exchange, self.connection.client.virtual_host or '/'))
        except KeyError:
            self.state.exchanges[exchange] = {
                'type': type,
                'durable': durable,
                'auto_delete': auto_delete,
                'arguments': arguments or {},
                'table': [],
            }

    def exchange_delete(self, exchange, if_unused=False, nowait=False):
        """Delete `exchange` and all its bindings."""
        for rkey, _, queue in self.get_table(exchange):
            self.queue_delete(queue, if_unused=True, if_empty=True)
        self.state.exchanges.pop(exchange, None)

    def queue_declare(self, queue=None, passive=False, **kwargs):
        """Declare queue."""
        queue = queue or 'amq.gen-%s' % uuid()
        if passive and not self._has_queue(queue, **kwargs):
            raise StdChannelError(
                '404',
                u'NOT_FOUND - no queue %r in vhost %r' % (
                    queue, self.connection.client.virtual_host or '/'),
                (50, 10), 'Channel.queue_declare')
        else:
            self._new_queue(queue, **kwargs)
        return queue, self._size(queue), 0

    def queue_delete(self, queue, if_unusued=False, if_empty=False, **kwargs):
        """Delete queue."""
        if if_empty and self._size(queue):
            return
        try:
            exchange, routing_key, arguments = self.state.bindings[queue]
        except KeyError:
            return
        meta = self.typeof(exchange).prepare_bind(queue, exchange,
                                                  routing_key, arguments)
        self._delete(queue, exchange, *meta)
        self.state.bindings.pop(queue, None)

    def after_reply_message_received(self, queue):
        self.queue_delete(queue)

    def exchange_bind(self, destination, source='', routing_key='',
                      nowait=False, arguments=None):
        raise NotImplementedError('transport does not support exchange_bind')

    def exchange_unbind(self, destination, source='', routing_key='',
                        nowait=False, arguments=None):
        raise NotImplementedError('transport does not support exchange_unbind')

    def queue_bind(self, queue, exchange=None, routing_key='',
                   arguments=None, **kwargs):
        """Bind `queue` to `exchange` with `routing key`."""
        if queue in self.state.bindings:
            return
        exchange = exchange or 'amq.direct'
        table = self.state.exchanges[exchange].setdefault('table', [])
        self.state.bindings[queue] = exchange, routing_key, arguments
        meta = self.typeof(exchange).prepare_bind(queue,
                                                  exchange,
                                                  routing_key,
                                                  arguments)
        table.append(meta)
        if self.supports_fanout:
            self._queue_bind(exchange, *meta)

    def queue_unbind(self, queue, exchange=None, routing_key='',
                     arguments=None, **kwargs):
        raise NotImplementedError('transport does not support queue_unbind')

    def list_bindings(self):
        for exchange in self.state.exchanges:
            table = self.get_table(exchange)
            for routing_key, pattern, queue in table:
                yield queue, exchange, routing_key

    def queue_purge(self, queue, **kwargs):
        """Remove all ready messages from queue."""
        return self._purge(queue)

    def basic_publish(self, message, exchange, routing_key, **kwargs):
        """Publish message."""
        props = message['properties']
        message['body'], props['body_encoding'] = \
            self.encode_body(message['body'], self.body_encoding)
        props['delivery_info']['exchange'] = exchange
        props['delivery_info']['routing_key'] = routing_key
        props['delivery_tag'] = self._next_delivery_tag()
        self.typeof(exchange).deliver(message,
                                      exchange, routing_key, **kwargs)

    def basic_consume(self, queue, no_ack, callback, consumer_tag, **kwargs):
        """Consume from `queue`"""
        self._tag_to_queue[consumer_tag] = queue
        self._active_queues.append(queue)

        def _callback(raw_message):
            message = self.Message(self, raw_message)
            if not no_ack:
                self.qos.append(message, message.delivery_tag)
            return callback(message)

        self.connection._callbacks[queue] = _callback
        self._consumers.add(consumer_tag)

        self._reset_cycle()

    def basic_cancel(self, consumer_tag):
        """Cancel consumer by consumer tag."""
        if consumer_tag in self._consumers:
            self._consumers.remove(consumer_tag)
            self._reset_cycle()
            queue = self._tag_to_queue.pop(consumer_tag, None)
            try:
                self._active_queues.remove(queue)
            except ValueError:
                pass
            self.connection._callbacks.pop(queue, None)

    def basic_get(self, queue, no_ack=False, **kwargs):
        """Get message by direct access (synchronous)."""
        try:
            message = self.Message(self, self._get(queue))
            if not no_ack:
                self.qos.append(message, message.delivery_tag)
            return message
        except Empty:
            pass

    def basic_ack(self, delivery_tag):
        """Acknowledge message."""
        self.qos.ack(delivery_tag)

    def basic_recover(self, requeue=False):
        """Recover unacked messages."""
        if requeue:
            return self.qos.restore_unacked()
        raise NotImplementedError('Does not support recover(requeue=False)')

    def basic_reject(self, delivery_tag, requeue=False):
        """Reject message."""
        self.qos.reject(delivery_tag, requeue=requeue)

    def basic_qos(self, prefetch_size=0, prefetch_count=0,
                  apply_global=False):
        """Change QoS settings for this channel.

        Only `prefetch_count` is supported.

        """
        self.qos.prefetch_count = prefetch_count

    def get_exchanges(self):
        return list(self.state.exchanges)

    def get_table(self, exchange):
        """Get table of bindings for `exchange`."""
        return self.state.exchanges[exchange]['table']

    def typeof(self, exchange, default='direct'):
        """Get the exchange type instance for `exchange`."""
        try:
            type = self.state.exchanges[exchange]['type']
        except KeyError:
            type = default
        return self.exchange_types[type]

    def _lookup(self, exchange, routing_key, default=None):
        """Find all queues matching `routing_key` for the given `exchange`.

        Returns `default` if no queues matched.

        """
        if default is None:
            default = self.deadletter_queue
        try:
            R = self.typeof(exchange).lookup(self.get_table(exchange),
                                             exchange, routing_key, default)
        except KeyError:
            R = []

        if not R and default is not None:
            warnings.warn(UndeliverableWarning(UNDELIVERABLE_FMT % {
                'exchange': exchange, 'routing_key': routing_key}))
            self._new_queue(default)
            R = [default]
        return R

    def _restore(self, message):
        """Redeliver message to its original destination."""
        delivery_info = message.delivery_info
        message = message.serializable()
        message['redelivered'] = True
        for queue in self._lookup(delivery_info['exchange'],
                                  delivery_info['routing_key']):
            self._put(queue, message)

    def drain_events(self, timeout=None):
        if self._consumers and self.qos.can_consume():
            if hasattr(self, '_get_many'):
                return self._get_many(self._active_queues, timeout=timeout)
            return self._poll(self.cycle, timeout=timeout)
        raise Empty()

    def message_to_python(self, raw_message):
        """Convert raw message to :class:`Message` instance."""
        if not isinstance(raw_message, self.Message):
            return self.Message(self, payload=raw_message)
        return raw_message

    def prepare_message(self, body, priority=None, content_type=None,
                        content_encoding=None, headers=None, properties=None):
        """Prepare message data."""
        properties = properties or {}
        info = properties.setdefault('delivery_info', {})
        info['priority'] = priority or 0

        return {'body': body,
                'content-encoding': content_encoding,
                'content-type': content_type,
                'headers': headers or {},
                'properties': properties or {}}

    def flow(self, active=True):
        """Enable/disable message flow.

        :raises NotImplementedError: as flow
            is not implemented by the base virtual implementation.

        """
        raise NotImplementedError('virtual channels does not support flow.')

    def close(self):
        """Close channel, cancel all consumers, and requeue unacked
        messages."""
        if not self.closed:
            self.closed = True
            for consumer in list(self._consumers):
                self.basic_cancel(consumer)
            if self._qos:
                self._qos.restore_unacked_once()
            if self._cycle is not None:
                self._cycle.close()
                self._cycle = None
            if self.connection is not None:
                self.connection.close_channel(self)
        self.exchange_types = None

    def encode_body(self, body, encoding=None):
        if encoding:
            return self.codecs.get(encoding).encode(body), encoding
        return body, encoding

    def decode_body(self, body, encoding=None):
        if encoding:
            return self.codecs.get(encoding).decode(body)
        return body

    def _reset_cycle(self):
        self._cycle = FairCycle(self._get, self._active_queues, Empty)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    @property
    def state(self):
        """Broker state containing exchanges and bindings."""
        return self.connection.state

    @property
    def qos(self):
        """:class:`QoS` manager for this channel."""
        if self._qos is None:
            self._qos = self.QoS(self)
        return self._qos

    @property
    def cycle(self):
        if self._cycle is None:
            self._reset_cycle()
        return self._cycle


class Management(base.Management):

    def __init__(self, transport):
        super(Management, self).__init__(transport)
        self.channel = transport.client.channel()

    def get_bindings(self):
        return [dict(destination=q, source=e, routing_key=r)
                for q, e, r in self.channel.list_bindings()]

    def close(self):
        self.channel.close()


class Transport(base.Transport):
    """Virtual transport.

    :param client: :class:`~kombu.Connection` instance

    """
    Channel = Channel
    Cycle = FairCycle
    Management = Management

    #: :class:`BrokerState` containing declared exchanges and
    #: bindings (set by constructor).
    state = BrokerState()

    #: :class:`~kombu.transport.virtual.scheduling.FairCycle` instance
    #: used to fairly drain events from channels (set by constructor).
    cycle = None

    #: port number used when no port is specified.
    default_port = None

    #: active channels.
    channels = None

    #: queue/callback map.
    _callbacks = None

    #: Time to sleep between unsuccessful polls.
    polling_interval = 1.0

    def __init__(self, client, **kwargs):
        self.client = client
        self.channels = []
        self._avail_channels = []
        self._callbacks = {}
        self.cycle = self.Cycle(self._drain_channel, self.channels, Empty)
        self._next_channel_id = count(1).next
        polling_interval = client.transport_options.get('polling_interval')
        if polling_interval is not None:
            self.polling_interval = polling_interval

    def create_channel(self, connection):
        try:
            return self._avail_channels.pop()
        except IndexError:
            channel = self.Channel(connection)
            self.channels.append(channel)
            return channel

    def close_channel(self, channel):
        try:
            try:
                self.channels.remove(channel)
            except ValueError:
                pass
        finally:
            channel.connection = None

    def establish_connection(self):
        # creates channel to verify connection.
        # this channel is then used as the next requested channel.
        # (returned by ``create_channel``).
        self._avail_channels.append(self.create_channel(self))
        return self     # for drain events

    def close_connection(self, connection):
        self.cycle.close()
        for l in self._avail_channels, self.channels:
            while l:
                try:
                    channel = l.pop()
                except (IndexError, KeyError):  # pragma: no cover
                    pass
                else:
                    channel.close()

    def drain_events(self, connection, timeout=None):
        loop = 0
        time_start = time()
        get = self.cycle.get
        polling_interval = self.polling_interval
        while 1:
            try:
                item, channel = get(timeout=timeout)
            except Empty:
                if timeout and time() - time_start >= timeout:
                    raise socket.timeout()
                loop += 1
                if polling_interval is not None:
                    sleep(polling_interval)
            else:
                break

        message, queue = item

        if not queue or queue not in self._callbacks:
            raise KeyError(
                "Received message for queue '%s' without consumers: %s" % (
                    queue, message))

        self._callbacks[queue](message)

    def _drain_channel(self, channel, timeout=None):
        return channel.drain_events(timeout=timeout)

    @property
    def default_connection_params(self):
        return {'port': self.default_port, 'hostname': 'localhost'}
