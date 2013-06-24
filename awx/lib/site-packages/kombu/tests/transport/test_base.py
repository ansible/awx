from __future__ import absolute_import
from __future__ import with_statement

from kombu import Connection, Consumer, Exchange, Producer, Queue
from kombu.transport.base import Message, StdChannel, Transport

from kombu.tests.utils import TestCase
from kombu.tests.utils import Mock


class test_StdChannel(TestCase):

    def setUp(self):
        self.conn = Connection('memory://')
        self.channel = self.conn.channel()
        self.channel.queues.clear()
        self.conn.connection.state.clear()

    def test_Consumer(self):
        q = Queue('foo', Exchange('foo'))
        print(self.channel.queues)
        cons = self.channel.Consumer(q)
        self.assertIsInstance(cons, Consumer)
        self.assertIs(cons.channel, self.channel)

    def test_Producer(self):
        prod = self.channel.Producer()
        self.assertIsInstance(prod, Producer)
        self.assertIs(prod.channel, self.channel)

    def test_interface_get_bindings(self):
        with self.assertRaises(NotImplementedError):
            StdChannel().get_bindings()

    def test_interface_after_reply_message_received(self):
        self.assertIsNone(
            StdChannel().after_reply_message_received(Queue('foo')),
        )


class test_Message(TestCase):

    def setUp(self):
        self.conn = Connection('memory://')
        self.channel = self.conn.channel()
        self.message = Message(self.channel, delivery_tag=313)

    def test_ack_respects_no_ack_consumers(self):
        self.channel.no_ack_consumers = set(['abc'])
        self.message.delivery_info['consumer_tag'] = 'abc'
        ack = self.channel.basic_ack = Mock()

        self.message.ack()
        self.assertNotEqual(self.message._state, 'ACK')
        self.assertFalse(ack.called)

    def test_ack_missing_consumer_tag(self):
        self.channel.no_ack_consumers = set(['abc'])
        self.message.delivery_info = {}
        ack = self.channel.basic_ack = Mock()

        self.message.ack()
        ack.assert_called_with(self.message.delivery_tag)

    def test_ack_not_no_ack(self):
        self.channel.no_ack_consumers = set()
        self.message.delivery_info['consumer_tag'] = 'abc'
        ack = self.channel.basic_ack = Mock()

        self.message.ack()
        ack.assert_called_with(self.message.delivery_tag)

    def test_ack_log_error_when_no_error(self):
        ack = self.message.ack = Mock()
        self.message.ack_log_error(Mock(), KeyError)
        ack.assert_called_with()

    def test_ack_log_error_when_error(self):
        ack = self.message.ack = Mock()
        ack.side_effect = KeyError('foo')
        logger = Mock()
        self.message.ack_log_error(logger, KeyError)
        ack.assert_called_with()
        self.assertTrue(logger.critical.called)
        self.assertIn("Couldn't ack", logger.critical.call_args[0][0])


class test_interface(TestCase):

    def test_establish_connection(self):
        with self.assertRaises(NotImplementedError):
            Transport(None).establish_connection()

    def test_close_connection(self):
        with self.assertRaises(NotImplementedError):
            Transport(None).close_connection(None)

    def test_create_channel(self):
        with self.assertRaises(NotImplementedError):
            Transport(None).create_channel(None)

    def test_close_channel(self):
        with self.assertRaises(NotImplementedError):
            Transport(None).close_channel(None)

    def test_drain_events(self):
        with self.assertRaises(NotImplementedError):
            Transport(None).drain_events(None)
