from __future__ import absolute_import
from __future__ import with_statement

import socket

from kombu import Connection
from kombu import pidbox
from kombu.utils import uuid

from .utils import TestCase
from .utils import Mock


class test_Mailbox(TestCase):

    def _handler(self, state):
        return self.stats['var']

    def setUp(self):

        class Mailbox(pidbox.Mailbox):

            def _collect(self, *args, **kwargs):
                return 'COLLECTED'

        self.mailbox = Mailbox('test_pidbox')
        self.connection = Connection(transport='memory')
        self.state = {'var': 1}
        self.handlers = {'mymethod': self._handler}
        self.bound = self.mailbox(self.connection)
        self.default_chan = self.connection.channel()
        self.node = self.bound.Node(
            'test_pidbox',
            state=self.state, handlers=self.handlers,
            channel=self.default_chan,
        )

    def test_reply__collect(self):
        mailbox = pidbox.Mailbox('test_reply__collect')(self.connection)
        exchange = mailbox.reply_exchange.name
        channel = self.connection.channel()
        mailbox.reply_queue(channel).declare()

        ticket = uuid()
        mailbox._publish_reply({'foo': 'bar'}, exchange, mailbox.oid, ticket)
        _callback_called = [False]

        def callback(body):
            _callback_called[0] = True

        reply = mailbox._collect(ticket, limit=1,
                                 callback=callback, channel=channel)
        self.assertEqual(reply, [{'foo': 'bar'}])
        self.assertTrue(_callback_called[0])

        ticket = uuid()
        mailbox._publish_reply({'biz': 'boz'}, exchange, mailbox.oid, ticket)
        reply = mailbox._collect(ticket, limit=1, channel=channel)
        self.assertEqual(reply, [{'biz': 'boz'}])

        de = mailbox.connection.drain_events = Mock()
        de.side_effect = socket.timeout
        mailbox._collect(ticket, limit=1, channel=channel)

    def test_constructor(self):
        self.assertIsNone(self.mailbox.connection)
        self.assertTrue(self.mailbox.exchange.name)
        self.assertTrue(self.mailbox.reply_exchange.name)

    def test_bound(self):
        bound = self.mailbox(self.connection)
        self.assertIs(bound.connection, self.connection)

    def test_Node(self):
        self.assertTrue(self.node.hostname)
        self.assertTrue(self.node.state)
        self.assertIs(self.node.mailbox, self.bound)
        self.assertTrue(self.handlers)

        # No initial handlers
        node2 = self.bound.Node('test_pidbox2', state=self.state)
        self.assertDictEqual(node2.handlers, {})

    def test_Node_consumer(self):
        consumer1 = self.node.Consumer()
        self.assertIs(consumer1.channel, self.default_chan)
        self.assertTrue(consumer1.no_ack)

        chan2 = self.connection.channel()
        consumer2 = self.node.Consumer(channel=chan2, no_ack=False)
        self.assertIs(consumer2.channel, chan2)
        self.assertFalse(consumer2.no_ack)

    def test_handler(self):
        node = self.bound.Node('test_handler', state=self.state)

        @node.handler
        def my_handler_name(state):
            return 42

        self.assertIn('my_handler_name', node.handlers)

    def test_dispatch(self):
        node = self.bound.Node('test_dispatch', state=self.state)

        @node.handler
        def my_handler_name(state, x=None, y=None):
            return x + y

        self.assertEqual(node.dispatch('my_handler_name',
                                       arguments={'x': 10, 'y': 10}), 20)

    def test_dispatch_raising_SystemExit(self):
        node = self.bound.Node('test_dispatch_raising_SystemExit',
                               state=self.state)

        @node.handler
        def my_handler_name(state):
            raise SystemExit

        with self.assertRaises(SystemExit):
            node.dispatch('my_handler_name')

    def test_dispatch_raising(self):
        node = self.bound.Node('test_dispatch_raising', state=self.state)

        @node.handler
        def my_handler_name(state):
            raise KeyError('foo')

        res = node.dispatch('my_handler_name')
        self.assertIn('error', res)
        self.assertIn('KeyError', res['error'])

    def test_dispatch_replies(self):
        _replied = [False]

        def reply(data, **options):
            _replied[0] = True

        node = self.bound.Node('test_dispatch', state=self.state)
        node.reply = reply

        @node.handler
        def my_handler_name(state, x=None, y=None):
            return x + y

        node.dispatch('my_handler_name',
                      arguments={'x': 10, 'y': 10},
                      reply_to={'exchange': 'foo', 'routing_key': 'bar'})
        self.assertTrue(_replied[0])

    def test_reply(self):
        _replied = [(None, None, None)]

        def publish_reply(data, exchange, routing_key, ticket, **kwargs):
            _replied[0] = (data, exchange, routing_key, ticket)

        mailbox = self.mailbox(self.connection)
        mailbox._publish_reply = publish_reply
        node = mailbox.Node('test_reply')

        @node.handler
        def my_handler_name(state):
            return 42

        node.dispatch('my_handler_name',
                      reply_to={'exchange': 'exchange',
                                'routing_key': 'rkey'},
                      ticket='TICKET')
        data, exchange, routing_key, ticket = _replied[0]
        self.assertEqual(data, {'test_reply': 42})
        self.assertEqual(exchange, 'exchange')
        self.assertEqual(routing_key, 'rkey')
        self.assertEqual(ticket, 'TICKET')

    def test_handle_message(self):
        node = self.bound.Node('test_dispatch_from_message')

        @node.handler
        def my_handler_name(state, x=None, y=None):
            return x * y

        body = {'method': 'my_handler_name',
                'arguments': {'x': 64, 'y': 64}}

        self.assertEqual(node.handle_message(body, None), 64 * 64)

        # message not for me should not be processed.
        body['destination'] = ['some_other_node']
        self.assertIsNone(node.handle_message(body, None))

    def test_listen(self):
        consumer = self.node.listen()
        self.assertEqual(consumer.callbacks[0],
                         self.node.handle_message)
        self.assertEqual(consumer.channel, self.default_chan)

    def test_cast(self):
        self.bound.cast(['somenode'], 'mymethod')
        consumer = self.node.Consumer()
        self.assertIsCast(self.get_next(consumer))

    def test_abcast(self):
        self.bound.abcast('mymethod')
        consumer = self.node.Consumer()
        self.assertIsCast(self.get_next(consumer))

    def test_call_destination_must_be_sequence(self):
        with self.assertRaises(ValueError):
            self.bound.call('some_node', 'mymethod')

    def test_call(self):
        self.assertEqual(
            self.bound.call(['some_node'], 'mymethod'),
            'COLLECTED',
        )
        consumer = self.node.Consumer()
        self.assertIsCall(self.get_next(consumer))

    def test_multi_call(self):
        self.assertEqual(self.bound.multi_call('mymethod'), 'COLLECTED')
        consumer = self.node.Consumer()
        self.assertIsCall(self.get_next(consumer))

    def get_next(self, consumer):
        m = consumer.queues[0].get()
        if m:
            return m.payload

    def assertIsCast(self, message):
        self.assertTrue(message['method'])

    def assertIsCall(self, message):
        self.assertTrue(message['method'])
        self.assertTrue(message['reply_to'])
