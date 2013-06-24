from __future__ import absolute_import
from __future__ import with_statement

import socket

from mock import patch

from kombu import common
from kombu.common import (
    Broadcast, maybe_declare,
    send_reply, isend_reply, collect_replies,
    declaration_cached, ignore_errors,
    QoS, PREFETCH_COUNT_MAX,
    entry_to_queue,
)
from kombu.exceptions import StdChannelError

from .utils import TestCase
from .utils import ContextMock, Mock, MockPool


class test_ignore_errors(TestCase):

    def test_ignored(self):
        connection = Mock()
        connection.channel_errors = (KeyError, )
        connection.connection_errors = (KeyError, )

        with ignore_errors(connection):
            raise KeyError()

        def raising():
            raise KeyError()

        ignore_errors(connection, raising)

        connection.channel_errors = connection.connection_errors = \
            ()

        with self.assertRaises(KeyError):
            with ignore_errors(connection):
                raise KeyError()


class test_declaration_cached(TestCase):

    def test_when_cached(self):
        chan = Mock()
        chan.connection.client.declared_entities = ['foo']
        self.assertTrue(declaration_cached('foo', chan))

    def test_when_not_cached(self):
        chan = Mock()
        chan.connection.client.declared_entities = ['bar']
        self.assertFalse(declaration_cached('foo', chan))


class test_Broadcast(TestCase):

    def test_arguments(self):
        q = Broadcast(name='test_Broadcast')
        self.assertTrue(q.name.startswith('bcast.'))
        self.assertEqual(q.alias, 'test_Broadcast')
        self.assertTrue(q.auto_delete)
        self.assertEqual(q.exchange.name, 'test_Broadcast')
        self.assertEqual(q.exchange.type, 'fanout')

        q = Broadcast('test_Broadcast', 'explicit_queue_name')
        self.assertEqual(q.name, 'explicit_queue_name')
        self.assertEqual(q.exchange.name, 'test_Broadcast')


class test_maybe_declare(TestCase):

    def test_cacheable(self):
        channel = Mock()
        client = channel.connection.client = Mock()
        client.declared_entities = set()
        entity = Mock()
        entity.can_cache_declaration = True
        entity.auto_delete = False
        entity.is_bound = True
        entity.channel = channel

        maybe_declare(entity, channel)
        self.assertEqual(entity.declare.call_count, 1)
        self.assertIn(entity, channel.connection.client.declared_entities)

        maybe_declare(entity, channel)
        self.assertEqual(entity.declare.call_count, 1)

        entity.channel.connection = None
        with self.assertRaises(StdChannelError):
            maybe_declare(entity)

    def test_binds_entities(self):
        channel = Mock()
        channel.connection.client.declared_entities = set()
        entity = Mock()
        entity.can_cache_declaration = True
        entity.is_bound = False
        entity.bind.return_value = entity
        entity.bind.return_value.channel = channel

        maybe_declare(entity, channel)
        entity.bind.assert_called_with(channel)

    def test_with_retry(self):
        channel = Mock()
        entity = Mock()
        entity.can_cache_declaration = True
        entity.is_bound = True
        entity.channel = channel

        maybe_declare(entity, channel, retry=True)
        self.assertTrue(channel.connection.client.ensure.call_count)


class test_replies(TestCase):

    def test_send_reply(self):
        req = Mock()
        req.content_type = 'application/json'
        req.properties = {'reply_to': 'hello',
                          'correlation_id': 'world'}
        channel = Mock()
        exchange = Mock()
        exchange.is_bound = True
        exchange.channel = channel
        producer = Mock()
        producer.channel = channel
        producer.channel.connection.client.declared_entities = set()
        send_reply(exchange, req, {'hello': 'world'}, producer)

        self.assertTrue(producer.publish.call_count)
        args = producer.publish.call_args
        self.assertDictEqual(args[0][0], {'hello': 'world'})
        self.assertDictEqual(args[1], {'exchange': exchange,
                                       'routing_key': 'hello',
                                       'correlation_id': 'world',
                                       'serializer': 'json'})

        exchange.declare.assert_called_with()

    @patch('kombu.common.ipublish')
    def test_isend_reply(self, ipublish):
        pool, exchange, req, msg, props = (Mock(), Mock(), Mock(),
                                           Mock(), Mock())

        isend_reply(pool, exchange, req, msg, props)
        ipublish.assert_called_with(pool, send_reply,
                                    (exchange, req, msg), props)

    @patch('kombu.common.itermessages')
    def test_collect_replies_with_ack(self, itermessages):
        conn, channel, queue = Mock(), Mock(), Mock()
        body, message = Mock(), Mock()
        itermessages.return_value = [(body, message)]
        it = collect_replies(conn, channel, queue, no_ack=False)
        m = it.next()
        self.assertIs(m, body)
        itermessages.assert_called_with(conn, channel, queue, no_ack=False)
        message.ack.assert_called_with()

        with self.assertRaises(StopIteration):
            it.next()

        channel.after_reply_message_received.assert_called_with(queue.name)

    @patch('kombu.common.itermessages')
    def test_collect_replies_no_ack(self, itermessages):
        conn, channel, queue = Mock(), Mock(), Mock()
        body, message = Mock(), Mock()
        itermessages.return_value = [(body, message)]
        it = collect_replies(conn, channel, queue)
        m = it.next()
        self.assertIs(m, body)
        itermessages.assert_called_with(conn, channel, queue, no_ack=True)
        self.assertFalse(message.ack.called)

    @patch('kombu.common.itermessages')
    def test_collect_replies_no_replies(self, itermessages):
        conn, channel, queue = Mock(), Mock(), Mock()
        itermessages.return_value = []
        it = collect_replies(conn, channel, queue)
        with self.assertRaises(StopIteration):
            it.next()

        self.assertFalse(channel.after_reply_message_received.called)


class test_insured(TestCase):

    @patch('kombu.common.logger')
    def test_ensure_errback(self, logger):
        common._ensure_errback('foo', 30)
        self.assertTrue(logger.error.called)

    def test_revive_connection(self):
        on_revive = Mock()
        channel = Mock()
        common.revive_connection(Mock(), channel, on_revive)
        on_revive.assert_called_with(channel)

        common.revive_connection(Mock(), channel, None)

    def test_revive_producer(self):
        on_revive = Mock()
        channel = Mock()
        common.revive_producer(Mock(), channel, on_revive)
        on_revive.assert_called_with(channel)

        common.revive_producer(Mock(), channel, None)

    def get_insured_mocks(self, insured_returns=('works', 'ignored')):
        conn = ContextMock()
        pool = MockPool(conn)
        fun = Mock()
        insured = conn.autoretry.return_value = Mock()
        insured.return_value = insured_returns
        return conn, pool, fun, insured

    def test_insured(self):
        conn, pool, fun, insured = self.get_insured_mocks()

        ret = common.insured(pool, fun, (2, 2), {'foo': 'bar'})
        self.assertEqual(ret, 'works')
        conn.ensure_connection.assert_called_with(
            errback=common._ensure_errback,
        )

        self.assertTrue(insured.called)
        i_args, i_kwargs = insured.call_args
        self.assertTupleEqual(i_args, (2, 2))
        self.assertDictEqual(i_kwargs, {'foo': 'bar',
                                        'connection': conn})

        self.assertTrue(conn.autoretry.called)
        ar_args, ar_kwargs = conn.autoretry.call_args
        self.assertTupleEqual(ar_args, (fun, conn.default_channel))
        self.assertTrue(ar_kwargs.get('on_revive'))
        self.assertTrue(ar_kwargs.get('errback'))

    def test_insured_custom_errback(self):
        conn, pool, fun, insured = self.get_insured_mocks()

        custom_errback = Mock()
        common.insured(pool, fun, (2, 2), {'foo': 'bar'},
                       errback=custom_errback)
        conn.ensure_connection.assert_called_with(errback=custom_errback)

    def get_ipublish_args(self, ensure_returns=None):
        producer = ContextMock()
        pool = MockPool(producer)
        fun = Mock()
        ensure_returns = ensure_returns or Mock()

        producer.connection.ensure.return_value = ensure_returns

        return producer, pool, fun, ensure_returns

    def test_ipublish(self):
        producer, pool, fun, ensure_returns = self.get_ipublish_args()
        ensure_returns.return_value = 'works'

        ret = common.ipublish(pool, fun, (2, 2), {'foo': 'bar'})
        self.assertEqual(ret, 'works')

        self.assertTrue(producer.connection.ensure.called)
        e_args, e_kwargs = producer.connection.ensure.call_args
        self.assertTupleEqual(e_args, (producer, fun))
        self.assertTrue(e_kwargs.get('on_revive'))
        self.assertEqual(e_kwargs.get('errback'), common._ensure_errback)

        ensure_returns.assert_called_with(2, 2, foo='bar', producer=producer)

    def test_ipublish_with_custom_errback(self):
        producer, pool, fun, _ = self.get_ipublish_args()

        errback = Mock()
        common.ipublish(pool, fun, (2, 2), {'foo': 'bar'}, errback=errback)
        _, e_kwargs = producer.connection.ensure.call_args
        self.assertEqual(e_kwargs.get('errback'), errback)


class MockConsumer(object):
    consumers = set()

    def __init__(self, channel, queues=None, callbacks=None, **kwargs):
        self.channel = channel
        self.queues = queues
        self.callbacks = callbacks

    def __enter__(self):
        self.consumers.add(self)
        return self

    def __exit__(self, *exc_info):
        self.consumers.discard(self)


class test_itermessages(TestCase):

    class MockConnection(object):
        should_raise_timeout = False

        def drain_events(self, **kwargs):
            if self.should_raise_timeout:
                raise socket.timeout()
            for consumer in MockConsumer.consumers:
                for callback in consumer.callbacks:
                    callback('body', 'message')

    def test_default(self):
        conn = self.MockConnection()
        channel = Mock()
        channel.connection.client = conn
        it = common.itermessages(conn, channel, 'q', limit=1,
                                 Consumer=MockConsumer)

        ret = it.next()
        self.assertTupleEqual(ret, ('body', 'message'))

        with self.assertRaises(StopIteration):
            it.next()

    def test_when_raises_socket_timeout(self):
        conn = self.MockConnection()
        conn.should_raise_timeout = True
        channel = Mock()
        channel.connection.client = conn
        it = common.itermessages(conn, channel, 'q', limit=1,
                                 Consumer=MockConsumer)

        with self.assertRaises(StopIteration):
            it.next()

    @patch('kombu.common.deque')
    def test_when_raises_IndexError(self, deque):
        deque_instance = deque.return_value = Mock()
        deque_instance.popleft.side_effect = IndexError()
        conn = self.MockConnection()
        channel = Mock()
        it = common.itermessages(conn, channel, 'q', limit=1,
                                 Consumer=MockConsumer)

        with self.assertRaises(StopIteration):
            it.next()


class test_entry_to_queue(TestCase):

    def test_calls_Queue_from_dict(self):
        with patch('kombu.common.Queue') as Queue:
            entry_to_queue('name', exchange='bar')
            Queue.from_dict.assert_called_with('name', exchange='bar')


class test_QoS(TestCase):

    class _QoS(QoS):
        def __init__(self, value):
            self.value = value
            QoS.__init__(self, None, value)

        def set(self, value):
            return value

    def test_qos_exceeds_16bit(self):
        with patch('kombu.common.logger') as logger:
            callback = Mock()
            qos = QoS(callback, 10)
            qos.prev = 100
            # cannot use 2 ** 32 because of a bug on OSX Py2.5:
            # https://jira.mongodb.org/browse/PYTHON-389
            qos.set(4294967296)
            self.assertTrue(logger.warn.called)
            callback.assert_called_with(prefetch_count=0)

    def test_qos_increment_decrement(self):
        qos = self._QoS(10)
        self.assertEqual(qos.increment_eventually(), 11)
        self.assertEqual(qos.increment_eventually(3), 14)
        self.assertEqual(qos.increment_eventually(-30), 14)
        self.assertEqual(qos.decrement_eventually(7), 7)
        self.assertEqual(qos.decrement_eventually(), 6)

    def test_qos_disabled_increment_decrement(self):
        qos = self._QoS(0)
        self.assertEqual(qos.increment_eventually(), 0)
        self.assertEqual(qos.increment_eventually(3), 0)
        self.assertEqual(qos.increment_eventually(-30), 0)
        self.assertEqual(qos.decrement_eventually(7), 0)
        self.assertEqual(qos.decrement_eventually(), 0)
        self.assertEqual(qos.decrement_eventually(10), 0)

    def test_qos_thread_safe(self):
        qos = self._QoS(10)

        def add():
            for i in range(1000):
                qos.increment_eventually()

        def sub():
            for i in range(1000):
                qos.decrement_eventually()

        def threaded(funs):
            from threading import Thread
            threads = [Thread(target=fun) for fun in funs]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        threaded([add, add])
        self.assertEqual(qos.value, 2010)

        qos.value = 1000
        threaded([add, sub])  # n = 2
        self.assertEqual(qos.value, 1000)

    def test_exceeds_short(self):
        qos = QoS(Mock(), PREFETCH_COUNT_MAX - 1)
        qos.update()
        self.assertEqual(qos.value, PREFETCH_COUNT_MAX - 1)
        qos.increment_eventually()
        self.assertEqual(qos.value, PREFETCH_COUNT_MAX)
        qos.increment_eventually()
        self.assertEqual(qos.value, PREFETCH_COUNT_MAX + 1)
        qos.decrement_eventually()
        self.assertEqual(qos.value, PREFETCH_COUNT_MAX)
        qos.decrement_eventually()
        self.assertEqual(qos.value, PREFETCH_COUNT_MAX - 1)

    def test_consumer_increment_decrement(self):
        mconsumer = Mock()
        qos = QoS(mconsumer.qos, 10)
        qos.update()
        self.assertEqual(qos.value, 10)
        mconsumer.qos.assert_called_with(prefetch_count=10)
        qos.decrement_eventually()
        qos.update()
        self.assertEqual(qos.value, 9)
        mconsumer.qos.assert_called_with(prefetch_count=9)
        qos.decrement_eventually()
        self.assertEqual(qos.value, 8)
        mconsumer.qos.assert_called_with(prefetch_count=9)
        self.assertIn({'prefetch_count': 9}, mconsumer.qos.call_args)

        # Does not decrement 0 value
        qos.value = 0
        qos.decrement_eventually()
        self.assertEqual(qos.value, 0)
        qos.increment_eventually()
        self.assertEqual(qos.value, 0)

    def test_consumer_decrement_eventually(self):
        mconsumer = Mock()
        qos = QoS(mconsumer.qos, 10)
        qos.decrement_eventually()
        self.assertEqual(qos.value, 9)
        qos.value = 0
        qos.decrement_eventually()
        self.assertEqual(qos.value, 0)

    def test_set(self):
        mconsumer = Mock()
        qos = QoS(mconsumer.qos, 10)
        qos.set(12)
        self.assertEqual(qos.prev, 12)
        qos.set(qos.prev)
