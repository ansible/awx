"""
kombu.transport.SQS
===================

Amazon SQS transport.

"""
from __future__ import absolute_import

import socket
import string

from Queue import Empty

from anyjson import loads, dumps

import boto
from boto import exception
from boto import sdb as _sdb
from boto import sqs as _sqs
from boto.sdb.domain import Domain
from boto.sdb.connection import SDBConnection
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message

from kombu.exceptions import StdConnectionError, StdChannelError
from kombu.utils import cached_property, uuid
from kombu.utils.encoding import safe_str

from . import virtual

# dots are replaced by dash, all other punctuation
# replaced by underscore.
CHARS_REPLACE_TABLE = dict((ord(c), 0x5f)
                           for c in string.punctuation if c not in '-_.')
CHARS_REPLACE_TABLE[0x2e] = 0x2d  # '.' -> '-'


def maybe_int(x):
    try:
        return int(x)
    except ValueError:
        return x
BOTO_VERSION = tuple(maybe_int(part) for part in boto.__version__.split('.'))
W_LONG_POLLING = BOTO_VERSION >= (2, 8)


class Table(Domain):
    """Amazon SimpleDB domain describing the message routing table."""
    # caches queues already bound, so we don't have to declare them again.
    _already_bound = set()

    def routes_for(self, exchange):
        """Iterator giving all routes for an exchange."""
        return self.select("""WHERE exchange = '%s'""" % exchange)

    def get_queue(self, queue):
        """Get binding for queue."""
        qid = self._get_queue_id(queue)
        if qid:
            return self.get_item(qid)

    def create_binding(self, queue):
        """Get binding item for queue.

        Creates the item if it doesn't exist.

        """
        item = self.get_queue(queue)
        if item:
            return item, item['id']
        id = uuid()
        return self.new_item(id), id

    def queue_bind(self, exchange, routing_key, pattern, queue):
        if queue not in self._already_bound:
            binding, id = self.create_binding(queue)
            binding.update(exchange=exchange,
                           routing_key=routing_key or '',
                           pattern=pattern or '',
                           queue=queue or '',
                           id=id)
            binding.save()
            self._already_bound.add(queue)

    def queue_delete(self, queue):
        """delete queue by name."""
        self._already_bound.discard(queue)
        item = self._get_queue_item(queue)
        if item:
            self.delete_item(item)

    def exchange_delete(self, exchange):
        """Delete all routes for `exchange`."""
        for item in self.routes_for(exchange):
            self.delete_item(item['id'])

    def get_item(self, item_name):
        """Uses `consistent_read` by default."""
        # Domain is an old-style class, can't use super().
        for consistent_read in (False, True):
            item = Domain.get_item(self, item_name, consistent_read)
            if item:
                return item

    def select(self, query='', next_token=None,
               consistent_read=True, max_items=None):
        """Uses `consistent_read` by default."""
        query = """SELECT * FROM `%s` %s""" % (self.name, query)
        return Domain.select(self, query, next_token,
                             consistent_read, max_items)

    def _try_first(self, query='', **kwargs):
        for c in (False, True):
            for item in self.select(query, consistent_read=c, **kwargs):
                return item

    def get_exchanges(self):
        return list(set(i['exchange'] for i in self.select()))

    def _get_queue_item(self, queue):
        return self._try_first("""WHERE queue = '%s' limit 1""" % queue)

    def _get_queue_id(self, queue):
        item = self._get_queue_item(queue)
        if item:
            return item['id']


class Channel(virtual.Channel):
    Table = Table

    default_region = 'us-east-1'
    default_visibility_timeout = 1800  # 30 minutes.
    # 20 seconds is the max value currently supported by SQS.
    default_wait_time_seconds = 1  # disabled: see Issue #198
    domain_format = 'kombu%(vhost)s'
    _sdb = None
    _sqs = None
    _queue_cache = {}
    _noack_queues = set()

    def __init__(self, *args, **kwargs):
        super(Channel, self).__init__(*args, **kwargs)

        # SQS blows up when you try to create a new queue if one already
        # exists with a different visibility_timeout, so this prepopulates
        # the queue_cache to protect us from recreating
        # queues that are known to already exist.
        queues = self.sqs.get_all_queues(prefix=self.queue_name_prefix)
        for queue in queues:
            self._queue_cache[queue.name] = queue

    def basic_consume(self, queue, no_ack, *args, **kwargs):
        if no_ack:
            self._noack_queues.add(queue)
        return super(Channel, self).basic_consume(queue, no_ack,
                                                  *args, **kwargs)

    def basic_cancel(self, consumer_tag):
        if consumer_tag in self._consumers:
            queue = self._tag_to_queue[consumer_tag]
            self._noack_queues.discard(queue)
        return super(Channel, self).basic_cancel(consumer_tag)

    def entity_name(self, name, table=CHARS_REPLACE_TABLE):
        """Format AMQP queue name into a legal SQS queue name."""
        return unicode(safe_str(name)).translate(table)

    def _new_queue(self, queue, **kwargs):
        """Ensures a queue exists in SQS."""
        # Translate to SQS name for consistency with initial
        # _queue_cache population.
        queue = self.entity_name(self.queue_name_prefix + queue)
        try:
            return self._queue_cache[queue]
        except KeyError:
            q = self._queue_cache[queue] = self.sqs.create_queue(
                queue, self.visibility_timeout,
            )
            return q

    def _queue_bind(self, *args):
        """Bind ``queue`` to ``exchange`` with routing key.

        Route will be stored in SDB if so enabled.

        """
        if self.supports_fanout:
            self.table.queue_bind(*args)

    def get_table(self, exchange):
        """Get routing table.

        Retrieved from SDB if :attr:`supports_fanout`.

        """
        if self.supports_fanout:
            return [(r['routing_key'], r['pattern'], r['queue'])
                    for r in self.table.routes_for(exchange)]
        return super(Channel, self).get_table(exchange)

    def get_exchanges(self):
        if self.supports_fanout:
            return self.table.get_exchanges()
        return super(Channel, self).get_exchanges()

    def _delete(self, queue, *args):
        """delete queue by name."""
        self._queue_cache.pop(queue, None)
        if self.supports_fanout:
            self.table.queue_delete(queue)
        super(Channel, self)._delete(queue)

    def exchange_delete(self, exchange, **kwargs):
        """Delete exchange by name."""
        if self.supports_fanout:
            self.table.exchange_delete(exchange)
        super(Channel, self).exchange_delete(exchange, **kwargs)

    def _has_queue(self, queue, **kwargs):
        """Returns True if ``queue`` has been previously declared."""
        if self.supports_fanout:
            return bool(self.table.get_queue(queue))
        return super(Channel, self)._has_queue(queue)

    def _put(self, queue, message, **kwargs):
        """Put message onto queue."""
        q = self._new_queue(queue)
        m = Message()
        m.set_body(dumps(message))
        q.write(m)

    def _put_fanout(self, exchange, message, **kwargs):
        """Deliver fanout message to all queues in ``exchange``."""
        for route in self.table.routes_for(exchange):
            self._put(route['queue'], message, **kwargs)

    def _get(self, queue):
        """Try to retrieve a single message off ``queue``."""
        q = self._new_queue(queue)
        if W_LONG_POLLING:
            rs = q.get_messages(1, wait_time_seconds=self.wait_time_seconds)
        else:  # boto < 2.8
            rs = q.get_messages(1)
        if rs:
            m = rs[0]
            payload = loads(rs[0].get_body())
            if queue in self._noack_queues:
                q.delete_message(m)
            else:
                payload['properties']['delivery_info'].update({
                    'sqs_message': m, 'sqs_queue': q, })
            return payload
        raise Empty()

    def _restore(self, message,
                 unwanted_delivery_info=('sqs_message', 'sqs_queue')):
        for unwanted_key in unwanted_delivery_info:
            # Remove objects that aren't JSON serializable (Issue #1108).
            message.delivery_info.pop(unwanted_key, None)
        return super(Channel, self)._restore(message)

    def basic_ack(self, delivery_tag):
        delivery_info = self.qos.get(delivery_tag).delivery_info
        try:
            queue = delivery_info['sqs_queue']
        except KeyError:
            pass
        else:
            queue.delete_message(delivery_info['sqs_message'])
        super(Channel, self).basic_ack(delivery_tag)

    def _size(self, queue):
        """Returns the number of messages in a queue."""
        return self._new_queue(queue).count()

    def _purge(self, queue):
        """Deletes all current messages in a queue."""
        q = self._new_queue(queue)
        # SQS is slow at registering messages, so run for a few
        # iterations to ensure messages are deleted.
        size = 0
        for i in xrange(10):
            size += q.count()
            if not size:
                break
        q.clear()
        return size

    def close(self):
        super(Channel, self).close()
        for conn in (self._sqs, self._sdb):
            if conn:
                try:
                    conn.close()
                except AttributeError, exc:  # FIXME ???
                    if "can't set attribute" not in str(exc):
                        raise

    def _get_regioninfo(self, regions):
        if self.region:
            for _r in regions:
                if _r.name == self.region:
                    return _r

    def _aws_connect_to(self, fun, regions):
        conninfo = self.conninfo
        region = self._get_regioninfo(regions)
        return fun(region=region,
                   aws_access_key_id=conninfo.userid,
                   aws_secret_access_key=conninfo.password,
                   port=conninfo.port)

    def _next_delivery_tag(self):
        return uuid()  # See #73

    @property
    def sqs(self):
        if self._sqs is None:
            self._sqs = self._aws_connect_to(SQSConnection, _sqs.regions())
        return self._sqs

    @property
    def sdb(self):
        if self._sdb is None:
            self._sdb = self._aws_connect_to(SDBConnection, _sdb.regions())
        return self._sdb

    @property
    def table(self):
        name = self.entity_name(
            self.domain_format % {'vhost': self.conninfo.virtual_host})
        d = self.sdb.get_object(
            'CreateDomain', {'DomainName': name}, self.Table)
        d.name = name
        return d

    @property
    def conninfo(self):
        return self.connection.client

    @property
    def transport_options(self):
        return self.connection.client.transport_options

    @cached_property
    def visibility_timeout(self):
        return (self.transport_options.get('visibility_timeout') or
                self.default_visibility_timeout)

    @cached_property
    def queue_name_prefix(self):
        return self.transport_options.get('queue_name_prefix', '')

    @cached_property
    def supports_fanout(self):
        return self.transport_options.get('sdb_persistence', False)

    @cached_property
    def region(self):
        return self.transport_options.get('region') or self.default_region

    @cached_property
    def wait_time_seconds(self):
        return (self.transport_options.get('wait_time_seconds') or
                self.default_wait_time_seconds)


class Transport(virtual.Transport):
    Channel = Channel

    polling_interval = 0
    wait_time_seconds = 20
    default_port = None
    connection_errors = (StdConnectionError, exception.SQSError, socket.error)
    channel_errors = (exception.SQSDecodeError, StdChannelError)
    driver_type = 'sqs'
    driver_name = 'sqs'
