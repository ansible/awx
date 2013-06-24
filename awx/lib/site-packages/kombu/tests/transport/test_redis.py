from __future__ import absolute_import
from __future__ import with_statement

import socket
import types

from anyjson import dumps
from collections import defaultdict
from itertools import count
from Queue import Empty, Queue as _Queue

from kombu import Connection, Exchange, Queue, Consumer, Producer
from kombu.exceptions import InconsistencyError, VersionMismatch
from kombu.utils import eventio  # patch poll

from kombu.tests.utils import TestCase
from kombu.tests.utils import Mock, module_exists, skip_if_not_module


class _poll(eventio._select):

    def poll(self, timeout):
        events = []
        for fd in self._rfd:
            if fd.data:
                events.append((fd.fileno(), eventio.READ))
        return events


eventio.poll = _poll
from kombu.transport import redis  # must import after poller patch


class ResponseError(Exception):
    pass


class Client(object):
    queues = {}
    sets = defaultdict(set)
    hashes = defaultdict(dict)
    shard_hint = None

    def __init__(self, db=None, port=None, connection_pool=None, **kwargs):
        self._called = []
        self._connection = None
        self.bgsave_raises_ResponseError = False
        self.connection = self._sconnection(self)

    def bgsave(self):
        self._called.append('BGSAVE')
        if self.bgsave_raises_ResponseError:
            raise ResponseError()

    def delete(self, key):
        self.queues.pop(key, None)

    def exists(self, key):
        return key in self.queues or key in self.sets

    def hset(self, key, k, v):
        self.hashes[key][k] = v

    def hget(self, key, k):
        return self.hashes[key].get(k)

    def hdel(self, key, k):
        self.hashes[key].pop(k, None)

    def sadd(self, key, member, *args):
        self.sets[key].add(member)
    zadd = sadd

    def smembers(self, key):
        return self.sets.get(key, set())

    def srem(self, key, *args):
        self.sets.pop(key, None)
    zrem = srem

    def llen(self, key):
        try:
            return self.queues[key].qsize()
        except KeyError:
            return 0

    def lpush(self, key, value):
        self.queues[key].put_nowait(value)

    def parse_response(self, connection, type, **options):
        cmd, queues = self.connection._sock.data.pop()
        assert cmd == type
        self.connection._sock.data = []
        if type == 'BRPOP':
            item = self.brpop(queues, 0.001)
            if item:
                return item
            raise Empty()

    def brpop(self, keys, timeout=None):
        key = keys[0]
        try:
            item = self.queues[key].get(timeout=timeout)
        except Empty:
            pass
        else:
            return key, item

    def rpop(self, key):
        try:
            return self.queues[key].get_nowait()
        except KeyError:
            pass

    def __contains__(self, k):
        return k in self._called

    def pipeline(self):
        return Pipeline(self)

    def encode(self, value):
        return str(value)

    def _new_queue(self, key):
        self.queues[key] = _Queue()

    class _sconnection(object):
        disconnected = False

        class _socket(object):
            blocking = True
            next_fileno = count(30).next

            def __init__(self, *args):
                self._fileno = self.next_fileno()
                self.data = []

            def fileno(self):
                return self._fileno

            def setblocking(self, blocking):
                self.blocking = blocking

        def __init__(self, client):
            self.client = client
            self._sock = self._socket()

        def disconnect(self):
            self.disconnected = True

        def send_command(self, cmd, *args):
            self._sock.data.append((cmd, args))

    def info(self):
        return {'foo': 1}

    def pubsub(self, *args, **kwargs):
        connection = self.connection

        class ConnectionPool(object):

            def get_connection(self, *args, **kwargs):
                return connection
        self.connection_pool = ConnectionPool()

        return self


class Pipeline(object):

    def __init__(self, client):
        self.client = client
        self.stack = []

    def __getattr__(self, key):
        if key not in self.__dict__:

            def _add(*args, **kwargs):
                self.stack.append((getattr(self.client, key), args, kwargs))
                return self

            return _add
        return self.__dict__[key]

    def execute(self):
        stack = list(self.stack)
        self.stack[:] = []
        return [fun(*args, **kwargs) for fun, args, kwargs in stack]


class Channel(redis.Channel):

    def _get_client(self):
        return Client

    def _get_pool(self):
        return Mock()

    def _get_response_error(self):
        return ResponseError

    def _new_queue(self, queue, **kwargs):
        self.client._new_queue(queue)

    def pipeline(self):
        return Pipeline(Client())


class Transport(redis.Transport):
    Channel = Channel

    def _get_errors(self):
        return ((KeyError, ), (IndexError, ))


class test_Channel(TestCase):

    def setUp(self):
        self.connection = Connection(transport=Transport)
        self.channel = self.connection.channel()

    def test_basic_consume_when_fanout_queue(self):
        self.channel.exchange_declare(exchange='txconfan', type='fanout')
        self.channel.queue_declare(queue='txconfanq')
        self.channel.queue_bind(queue='txconfanq', exchange='txconfan')

        self.assertIn('txconfanq', self.channel._fanout_queues)
        self.channel.basic_consume('txconfanq', False, None, 1)
        self.assertIn('txconfanq', self.channel.active_fanout_queues)
        self.assertEqual(self.channel._fanout_to_queue.get('txconfan'),
                         'txconfanq')

    def test_basic_cancel_unknown_delivery_tag(self):
        self.assertIsNone(self.channel.basic_cancel('txaseqwewq'))

    def test_subscribe_no_queues(self):
        self.channel.subclient = Mock()
        self.channel.active_fanout_queues.clear()
        self.channel._subscribe()

        self.assertFalse(self.channel.subclient.subscribe.called)

    def test_subscribe(self):
        self.channel.subclient = Mock()
        self.channel.active_fanout_queues.add('a')
        self.channel.active_fanout_queues.add('b')
        self.channel._fanout_queues.update(a='a', b='b')

        self.channel._subscribe()
        self.assertTrue(self.channel.subclient.subscribe.called)
        s_args, _ = self.channel.subclient.subscribe.call_args
        self.assertItemsEqual(s_args[0], ['a', 'b'])

        self.channel.subclient.connection._sock = None
        self.channel._subscribe()
        self.channel.subclient.connection.connect.assert_called_with()

    def test_handle_unsubscribe_message(self):
        s = self.channel.subclient
        s.subscribed = True
        self.channel._handle_message(s, ['unsubscribe', 'a', 0])
        self.assertFalse(s.subscribed)

    def test_handle_pmessage_message(self):
        self.assertDictEqual(
            self.channel._handle_message(
                self.channel.subclient,
                ['pmessage', 'pattern', 'channel', 'data'],
            ),
            {
                'type': 'pmessage',
                'pattern': 'pattern',
                'channel': 'channel',
                'data': 'data',
            },
        )

    def test_handle_message(self):
        self.assertDictEqual(
            self.channel._handle_message(
                self.channel.subclient,
                ['type', 'channel', 'data'],
            ),
            {
                'type': 'type',
                'pattern': None,
                'channel': 'channel',
                'data': 'data',
            },
        )

    def test_brpop_start_but_no_queues(self):
        self.assertIsNone(self.channel._brpop_start())

    def test_receive(self):
        s = self.channel.subclient = Mock()
        self.channel._fanout_to_queue['a'] = 'b'
        s.parse_response.return_value = ['message', 'a',
                                         dumps({'hello': 'world'})]
        payload, queue = self.channel._receive()
        self.assertDictEqual(payload, {'hello': 'world'})
        self.assertEqual(queue, 'b')

    def test_receive_raises(self):
        self.channel._in_listen = True
        s = self.channel.subclient = Mock()
        s.parse_response.side_effect = KeyError('foo')

        with self.assertRaises(redis.Empty):
            self.channel._receive()
        self.assertFalse(self.channel._in_listen)

    def test_receive_empty(self):
        s = self.channel.subclient = Mock()
        s.parse_response.return_value = None

        with self.assertRaises(redis.Empty):
            self.channel._receive()

    def test_receive_different_message_Type(self):
        s = self.channel.subclient = Mock()
        s.parse_response.return_value = ['pmessage', '/foo/', 0, 'data']

        with self.assertRaises(redis.Empty):
            self.channel._receive()

    def test_brpop_read_raises(self):
        c = self.channel.client = Mock()
        c.parse_response.side_effect = KeyError('foo')

        with self.assertRaises(redis.Empty):
            self.channel._brpop_read()

        c.connection.disconnect.assert_called_with()

    def test_brpop_read_gives_None(self):
        c = self.channel.client = Mock()
        c.parse_response.return_value = None

        with self.assertRaises(redis.Empty):
            self.channel._brpop_read()

    def test_poll_error(self):
        c = self.channel.client = Mock()
        c.parse_response = Mock()
        self.channel._poll_error('BRPOP')

        c.parse_response.assert_called_with('BRPOP')

        c.parse_response.side_effect = KeyError('foo')
        self.assertIsNone(self.channel._poll_error('BRPOP'))

    def test_put_fanout(self):
        self.channel._in_poll = False
        c = self.channel.client = Mock()

        body = {'hello': 'world'}
        self.channel._put_fanout('exchange', body)
        c.publish.assert_called_with('exchange', dumps(body))

    def test_delete(self):
        x = self.channel
        self.channel._in_poll = False
        delete = x.client.delete = Mock()
        srem = x.client.srem = Mock()

        x._delete('queue', 'exchange', 'routing_key', None)
        delete.assert_has_call('queue')
        srem.assert_has_call(x.keyprefix_queue % ('exchange', ),
                             x.sep.join(['routing_key', '', 'queue']))

    def test_has_queue(self):
        self.channel._in_poll = False
        exists = self.channel.client.exists = Mock()
        exists.return_value = True
        self.assertTrue(self.channel._has_queue('foo'))
        exists.assert_has_call('foo')

        exists.return_value = False
        self.assertFalse(self.channel._has_queue('foo'))

    def test_close_when_closed(self):
        self.channel.closed = True
        self.channel.close()

    def test_close_client_close_raises(self):
        c = self.channel.client = Mock()
        c.connection.disconnect.side_effect = self.channel.ResponseError()

        self.channel.close()
        c.connection.disconnect.assert_called_with()

    def test_invalid_database_raises_ValueError(self):

        with self.assertRaises(ValueError):
            self.channel.connection.client.virtual_host = 'dwqeq'
            self.channel._connparams()

    @skip_if_not_module('redis')
    def test_get_client(self):
        import redis as R
        KombuRedis = redis.Channel._get_client(self.channel)
        self.assertTrue(KombuRedis)

        Rv = getattr(R, 'VERSION', None)
        try:
            R.VERSION = (2, 4, 0)
            with self.assertRaises(VersionMismatch):
                redis.Channel._get_client(self.channel)
        finally:
            if Rv is not None:
                R.VERSION = Rv

    @skip_if_not_module('redis')
    def test_get_response_error(self):
        from redis.exceptions import ResponseError
        self.assertIs(redis.Channel._get_response_error(self.channel),
                      ResponseError)

    def test_avail_client_when_not_in_poll(self):
        self.channel._in_poll = False
        c = self.channel.client = Mock()

        with self.channel.conn_or_acquire() as client:
            self.assertIs(client, c)

    def test_avail_client_when_in_poll(self):
        self.channel._in_poll = True
        self.channel._pool = Mock()
        cc = self.channel._create_client = Mock()
        client = cc.return_value = Mock()

        with self.channel.conn_or_acquire():
            pass
        self.channel.pool.release.assert_called_with(client.connection)
        cc.assert_called_with()

    @skip_if_not_module('redis')
    def test_transport_get_errors(self):
        self.assertTrue(redis.Transport._get_errors(self.connection.transport))

    @skip_if_not_module('redis')
    def test_transport_get_errors_when_InvalidData_used(self):
        from redis import exceptions

        class ID(Exception):
            pass

        DataError = getattr(exceptions, 'DataError', None)
        InvalidData = getattr(exceptions, 'InvalidData', None)
        exceptions.InvalidData = ID
        exceptions.DataError = None
        try:
            errors = redis.Transport._get_errors(self.connection.transport)
            self.assertTrue(errors)
            self.assertIn(ID, errors[1])
        finally:
            if DataError is not None:
                exceptions.DataError = DataError
            if InvalidData is not None:
                exceptions.InvalidData = InvalidData

    def test_empty_queues_key(self):
        channel = self.channel
        channel._in_poll = False
        key = channel.keyprefix_queue % 'celery'

        # Everything is fine, there is a list of queues.
        channel.client.sadd(key, 'celery\x06\x16\x06\x16celery')
        self.assertListEqual(channel.get_table('celery'),
                             [('celery', '', 'celery')])

        # ... then for some reason, the _kombu.binding.celery key gets lost
        channel.client.srem(key)

        # which raises a channel error so that the consumer/publisher
        # can recover by redeclaring the required entities.
        with self.assertRaises(InconsistencyError):
            self.channel.get_table('celery')


class test_Redis(TestCase):

    def setUp(self):
        self.connection = Connection(transport=Transport)
        self.exchange = Exchange('test_Redis', type='direct')
        self.queue = Queue('test_Redis', self.exchange, 'test_Redis')

    def tearDown(self):
        self.connection.close()

    def test_publish__get(self):
        channel = self.connection.channel()
        producer = Producer(channel, self.exchange, routing_key='test_Redis')
        self.queue(channel).declare()

        producer.publish({'hello': 'world'})

        self.assertDictEqual(self.queue(channel).get().payload,
                             {'hello': 'world'})
        self.assertIsNone(self.queue(channel).get())
        self.assertIsNone(self.queue(channel).get())
        self.assertIsNone(self.queue(channel).get())

    def test_publish__consume(self):
        connection = Connection(transport=Transport)
        channel = connection.channel()
        producer = Producer(channel, self.exchange, routing_key='test_Redis')
        consumer = Consumer(channel, self.queue)

        producer.publish({'hello2': 'world2'})
        _received = []

        def callback(message_data, message):
            _received.append(message_data)
            message.ack()

        consumer.register_callback(callback)
        consumer.consume()

        self.assertIn(channel, channel.connection.cycle._channels)
        try:
            connection.drain_events(timeout=1)
            self.assertTrue(_received)
            with self.assertRaises(socket.timeout):
                connection.drain_events(timeout=0.01)
        finally:
            channel.close()

    def test_purge(self):
        channel = self.connection.channel()
        producer = Producer(channel, self.exchange, routing_key='test_Redis')
        self.queue(channel).declare()

        for i in range(10):
            producer.publish({'hello': 'world-%s' % (i, )})

        self.assertEqual(channel._size('test_Redis'), 10)
        self.assertEqual(self.queue(channel).purge(), 10)
        channel.close()

    def test_db_values(self):
        Connection(virtual_host=1,
                   transport=Transport).channel()

        Connection(virtual_host='1',
                   transport=Transport).channel()

        Connection(virtual_host='/1',
                   transport=Transport).channel()

        with self.assertRaises(Exception):
            Connection('redis:///foo').channel()

    def test_db_port(self):
        c1 = Connection(port=None, transport=Transport).channel()
        c1.close()

        c2 = Connection(port=9999, transport=Transport).channel()
        c2.close()

    def test_close_poller_not_active(self):
        c = Connection(transport=Transport).channel()
        cycle = c.connection.cycle
        c.client.connection
        c.close()
        self.assertNotIn(c, cycle._channels)

    def test_close_ResponseError(self):
        c = Connection(transport=Transport).channel()
        c.client.bgsave_raises_ResponseError = True
        c.close()

    def test_close_disconnects(self):
        c = Connection(transport=Transport).channel()
        conn1 = c.client.connection
        conn2 = c.subclient.connection
        c.close()
        self.assertTrue(conn1.disconnected)
        self.assertTrue(conn2.disconnected)

    def test_get__Empty(self):
        channel = self.connection.channel()
        with self.assertRaises(Empty):
            channel._get('does-not-exist')
        channel.close()

    def test_get_client(self):

        myredis, exceptions = _redis_modules()

        @module_exists(myredis, exceptions)
        def _do_test():
            conn = Connection(transport=Transport)
            chan = conn.channel()
            self.assertTrue(chan.Client)
            self.assertTrue(chan.ResponseError)
            self.assertTrue(conn.transport.connection_errors)
            self.assertTrue(conn.transport.channel_errors)

        _do_test()


def _redis_modules():

    class ConnectionError(Exception):
        pass

    class AuthenticationError(Exception):
        pass

    class InvalidData(Exception):
        pass

    class InvalidResponse(Exception):
        pass

    class ResponseError(Exception):
        pass

    exceptions = types.ModuleType('redis.exceptions')
    exceptions.ConnectionError = ConnectionError
    exceptions.AuthenticationError = AuthenticationError
    exceptions.InvalidData = InvalidData
    exceptions.InvalidResponse = InvalidResponse
    exceptions.ResponseError = ResponseError

    class Redis(object):
        pass

    myredis = types.ModuleType('redis')
    myredis.exceptions = exceptions
    myredis.Redis = Redis

    return myredis, exceptions


class test_MultiChannelPoller(TestCase):
    Poller = redis.MultiChannelPoller

    def test_close_unregisters_fds(self):
        p = self.Poller()
        poller = p.poller = Mock()
        p._chan_to_sock.update({1: 1, 2: 2, 3: 3})

        p.close()

        self.assertEqual(poller.unregister.call_count, 3)
        u_args = poller.unregister.call_args_list

        self.assertItemsEqual(u_args, [((1, ), {}),
                                       ((2, ), {}),
                                       ((3, ), {})])

    def test_close_when_unregister_raises_KeyError(self):
        p = self.Poller()
        p.poller = Mock()
        p._chan_to_sock.update({1: 1})
        p.poller.unregister.side_effect = KeyError(1)
        p.close()

    def test_close_resets_state(self):
        p = self.Poller()
        p.poller = Mock()
        p._channels = Mock()
        p._fd_to_chan = Mock()
        p._chan_to_sock = Mock()

        p._chan_to_sock.itervalues.return_value = []
        p._chan_to_sock.values.return_value = []  # py3k

        p.close()
        p._channels.clear.assert_called_with()
        p._fd_to_chan.clear.assert_called_with()
        p._chan_to_sock.clear.assert_called_with()
        self.assertIsNone(p.poller)

    def test_register_when_registered_reregisters(self):
        p = self.Poller()
        p.poller = Mock()
        channel, client, type = Mock(), Mock(), Mock()
        sock = client.connection._sock = Mock()
        sock.fileno.return_value = 10

        p._chan_to_sock = {(channel, client, type): 6}
        p._register(channel, client, type)
        p.poller.unregister.assert_called_with(6)
        self.assertTupleEqual(p._fd_to_chan[10], (channel, type))
        self.assertEqual(p._chan_to_sock[(channel, client, type)], sock)
        p.poller.register.assert_called_with(sock, p.eventflags)

        # when client not connected yet
        client.connection._sock = None

        def after_connected():
            client.connection._sock = Mock()
        client.connection.connect.side_effect = after_connected

        p._register(channel, client, type)
        client.connection.connect.assert_called_with()

    def test_register_BRPOP(self):
        p = self.Poller()
        channel = Mock()
        channel.client.connection._sock = None
        p._register = Mock()

        channel._in_poll = False
        p._register_BRPOP(channel)
        self.assertEqual(channel._brpop_start.call_count, 1)
        self.assertEqual(p._register.call_count, 1)

        channel.client.connection._sock = Mock()
        p._chan_to_sock[(channel, channel.client, 'BRPOP')] = True
        channel._in_poll = True
        p._register_BRPOP(channel)
        self.assertEqual(channel._brpop_start.call_count, 1)
        self.assertEqual(p._register.call_count, 1)

    def test_register_LISTEN(self):
        p = self.Poller()
        channel = Mock()
        channel.subclient.connection._sock = None
        channel._in_listen = False
        p._register = Mock()

        p._register_LISTEN(channel)
        p._register.assert_called_with(channel, channel.subclient, 'LISTEN')
        self.assertEqual(p._register.call_count, 1)
        self.assertEqual(channel._subscribe.call_count, 1)

        channel._in_listen = True
        channel.subclient.connection._sock = Mock()
        p._register_LISTEN(channel)
        self.assertEqual(p._register.call_count, 1)
        self.assertEqual(channel._subscribe.call_count, 1)

    def create_get(self, events=None, queues=None, fanouts=None):
        _pr = [] if events is None else events
        _aq = [] if queues is None else queues
        _af = [] if fanouts is None else fanouts
        p = self.Poller()
        p.poller = Mock()
        p.poller.poll.return_value = _pr

        p._register_BRPOP = Mock()
        p._register_LISTEN = Mock()

        channel = Mock()
        p._channels = [channel]
        channel.active_queues = _aq
        channel.active_fanout_queues = _af

        return p, channel

    def test_get_no_actions(self):
        p, channel = self.create_get()

        with self.assertRaises(redis.Empty):
            p.get()

    def test_get_brpop_qos_allow(self):
        p, channel = self.create_get(queues=['a_queue'])
        channel.qos.can_consume.return_value = True

        with self.assertRaises(redis.Empty):
            p.get()

        p._register_BRPOP.assert_called_with(channel)

    def test_get_brpop_qos_disallow(self):
        p, channel = self.create_get(queues=['a_queue'])
        channel.qos.can_consume.return_value = False

        with self.assertRaises(redis.Empty):
            p.get()

        self.assertFalse(p._register_BRPOP.called)

    def test_get_listen(self):
        p, channel = self.create_get(fanouts=['f_queue'])

        with self.assertRaises(redis.Empty):
            p.get()

        p._register_LISTEN.assert_called_with(channel)

    def test_get_receives_ERR(self):
        p, channel = self.create_get(events=[(1, eventio.ERR)])
        p._fd_to_chan[1] = (channel, 'BRPOP')

        with self.assertRaises(redis.Empty):
            p.get()

        channel._poll_error.assert_called_with('BRPOP')

    def test_get_receives_multiple(self):
        p, channel = self.create_get(events=[(1, eventio.ERR),
                                             (1, eventio.ERR)])
        p._fd_to_chan[1] = (channel, 'BRPOP')

        with self.assertRaises(redis.Empty):
            p.get()

        channel._poll_error.assert_called_with('BRPOP')
