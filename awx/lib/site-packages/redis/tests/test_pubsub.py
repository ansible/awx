from __future__ import with_statement
import pytest
import time

import redis
from redis.exceptions import ConnectionError
from redis._compat import basestring, u, unichr

from .conftest import r as _redis_client


def wait_for_message(pubsub, timeout=0.1, ignore_subscribe_messages=False):
    now = time.time()
    timeout = now + timeout
    while now < timeout:
        message = pubsub.get_message(
            ignore_subscribe_messages=ignore_subscribe_messages)
        if message is not None:
            return message
        time.sleep(0.01)
        now = time.time()
    return None


def make_message(type, channel, data, pattern=None):
    return {
        'type': type,
        'pattern': pattern and pattern.encode('utf-8') or None,
        'channel': channel.encode('utf-8'),
        'data': data.encode('utf-8') if isinstance(data, basestring) else data
    }


def make_subscribe_test_data(pubsub, type):
    if type == 'channel':
        return {
            'p': pubsub,
            'sub_type': 'subscribe',
            'unsub_type': 'unsubscribe',
            'sub_func': pubsub.subscribe,
            'unsub_func': pubsub.unsubscribe,
            'keys': ['foo', 'bar', u('uni') + unichr(4456) + u('code')]
        }
    elif type == 'pattern':
        return {
            'p': pubsub,
            'sub_type': 'psubscribe',
            'unsub_type': 'punsubscribe',
            'sub_func': pubsub.psubscribe,
            'unsub_func': pubsub.punsubscribe,
            'keys': ['f*', 'b*', u('uni') + unichr(4456) + u('*')]
        }
    assert False, 'invalid subscribe type: %s' % type


class TestPubSubSubscribeUnsubscribe(object):

    def _test_subscribe_unsubscribe(self, p, sub_type, unsub_type, sub_func,
                                    unsub_func, keys):
        for key in keys:
            assert sub_func(key) is None

        # should be a message for each channel/pattern we just subscribed to
        for i, key in enumerate(keys):
            assert wait_for_message(p) == make_message(sub_type, key, i + 1)

        for key in keys:
            assert unsub_func(key) is None

        # should be a message for each channel/pattern we just unsubscribed
        # from
        for i, key in enumerate(keys):
            i = len(keys) - 1 - i
            assert wait_for_message(p) == make_message(unsub_type, key, i)

    def test_channel_subscribe_unsubscribe(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), 'channel')
        self._test_subscribe_unsubscribe(**kwargs)

    def test_pattern_subscribe_unsubscribe(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), 'pattern')
        self._test_subscribe_unsubscribe(**kwargs)

    def _test_resubscribe_on_reconnection(self, p, sub_type, unsub_type,
                                          sub_func, unsub_func, keys):

        for key in keys:
            assert sub_func(key) is None

        # should be a message for each channel/pattern we just subscribed to
        for i, key in enumerate(keys):
            assert wait_for_message(p) == make_message(sub_type, key, i + 1)

        # manually disconnect
        p.connection.disconnect()

        # calling get_message again reconnects and resubscribes
        # note, we may not re-subscribe to channels in exactly the same order
        # so we have to do some extra checks to make sure we got them all
        messages = []
        for i in range(len(keys)):
            messages.append(wait_for_message(p))

        unique_channels = set()
        assert len(messages) == len(keys)
        for i, message in enumerate(messages):
            assert message['type'] == sub_type
            assert message['data'] == i + 1
            assert isinstance(message['channel'], bytes)
            channel = message['channel'].decode('utf-8')
            unique_channels.add(channel)

        assert len(unique_channels) == len(keys)
        for channel in unique_channels:
            assert channel in keys

    def test_resubscribe_to_channels_on_reconnection(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), 'channel')
        self._test_resubscribe_on_reconnection(**kwargs)

    def test_resubscribe_to_patterns_on_reconnection(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), 'pattern')
        self._test_resubscribe_on_reconnection(**kwargs)

    def _test_subscribed_property(self, p, sub_type, unsub_type, sub_func,
                                  unsub_func, keys):

        assert p.subscribed is False
        sub_func(keys[0])
        # we're now subscribed even though we haven't processed the
        # reply from the server just yet
        assert p.subscribed is True
        assert wait_for_message(p) == make_message(sub_type, keys[0], 1)
        # we're still subscribed
        assert p.subscribed is True

        # unsubscribe from all channels
        unsub_func()
        # we're still technically subscribed until we process the
        # response messages from the server
        assert p.subscribed is True
        assert wait_for_message(p) == make_message(unsub_type, keys[0], 0)
        # now we're no longer subscribed as no more messages can be delivered
        # to any channels we were listening to
        assert p.subscribed is False

        # subscribing again flips the flag back
        sub_func(keys[0])
        assert p.subscribed is True
        assert wait_for_message(p) == make_message(sub_type, keys[0], 1)

        # unsubscribe again
        unsub_func()
        assert p.subscribed is True
        # subscribe to another channel before reading the unsubscribe response
        sub_func(keys[1])
        assert p.subscribed is True
        # read the unsubscribe for key1
        assert wait_for_message(p) == make_message(unsub_type, keys[0], 0)
        # we're still subscribed to key2, so subscribed should still be True
        assert p.subscribed is True
        # read the key2 subscribe message
        assert wait_for_message(p) == make_message(sub_type, keys[1], 1)
        unsub_func()
        # haven't read the message yet, so we're still subscribed
        assert p.subscribed is True
        assert wait_for_message(p) == make_message(unsub_type, keys[1], 0)
        # now we're finally unsubscribed
        assert p.subscribed is False

    def test_subscribe_property_with_channels(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), 'channel')
        self._test_subscribed_property(**kwargs)

    def test_subscribe_property_with_patterns(self, r):
        kwargs = make_subscribe_test_data(r.pubsub(), 'pattern')
        self._test_subscribed_property(**kwargs)

    def test_ignore_all_subscribe_messages(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)

        checks = (
            (p.subscribe, 'foo'),
            (p.unsubscribe, 'foo'),
            (p.psubscribe, 'f*'),
            (p.punsubscribe, 'f*'),
        )

        assert p.subscribed is False
        for func, channel in checks:
            assert func(channel) is None
            assert p.subscribed is True
            assert wait_for_message(p) is None
        assert p.subscribed is False

    def test_ignore_individual_subscribe_messages(self, r):
        p = r.pubsub()

        checks = (
            (p.subscribe, 'foo'),
            (p.unsubscribe, 'foo'),
            (p.psubscribe, 'f*'),
            (p.punsubscribe, 'f*'),
        )

        assert p.subscribed is False
        for func, channel in checks:
            assert func(channel) is None
            assert p.subscribed is True
            message = wait_for_message(p, ignore_subscribe_messages=True)
            assert message is None
        assert p.subscribed is False


class TestPubSubMessages(object):
    def setup_method(self, method):
        self.message = None

    def message_handler(self, message):
        self.message = message

    def test_published_message_to_channel(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.subscribe('foo')
        assert r.publish('foo', 'test message') == 1

        message = wait_for_message(p)
        assert isinstance(message, dict)
        assert message == make_message('message', 'foo', 'test message')

    def test_published_message_to_pattern(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.subscribe('foo')
        p.psubscribe('f*')
        # 1 to pattern, 1 to channel
        assert r.publish('foo', 'test message') == 2

        message1 = wait_for_message(p)
        message2 = wait_for_message(p)
        assert isinstance(message1, dict)
        assert isinstance(message2, dict)

        expected = [
            make_message('message', 'foo', 'test message'),
            make_message('pmessage', 'foo', 'test message', pattern='f*')
        ]

        assert message1 in expected
        assert message2 in expected
        assert message1 != message2

    def test_channel_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.subscribe(foo=self.message_handler)
        assert r.publish('foo', 'test message') == 1
        assert wait_for_message(p) is None
        assert self.message == make_message('message', 'foo', 'test message')

    def test_pattern_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.psubscribe(**{'f*': self.message_handler})
        assert r.publish('foo', 'test message') == 1
        assert wait_for_message(p) is None
        assert self.message == make_message('pmessage', 'foo', 'test message',
                                            pattern='f*')

    def test_unicode_channel_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        channel = u('uni') + unichr(4456) + u('code')
        channels = {channel: self.message_handler}
        p.subscribe(**channels)
        assert r.publish(channel, 'test message') == 1
        assert wait_for_message(p) is None
        assert self.message == make_message('message', channel, 'test message')

    def test_unicode_pattern_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        pattern = u('uni') + unichr(4456) + u('*')
        channel = u('uni') + unichr(4456) + u('code')
        p.psubscribe(**{pattern: self.message_handler})
        assert r.publish(channel, 'test message') == 1
        assert wait_for_message(p) is None
        assert self.message == make_message('pmessage', channel,
                                            'test message', pattern=pattern)


class TestPubSubAutoDecoding(object):
    "These tests only validate that we get unicode values back"

    channel = u('uni') + unichr(4456) + u('code')
    pattern = u('uni') + unichr(4456) + u('*')
    data = u('abc') + unichr(4458) + u('123')

    def make_message(self, type, channel, data, pattern=None):
        return {
            'type': type,
            'channel': channel,
            'pattern': pattern,
            'data': data
        }

    def setup_method(self, method):
        self.message = None

    def message_handler(self, message):
        self.message = message

    @pytest.fixture()
    def r(self, request):
        return _redis_client(request=request, decode_responses=True)

    def test_channel_subscribe_unsubscribe(self, r):
        p = r.pubsub()
        p.subscribe(self.channel)
        assert wait_for_message(p) == self.make_message('subscribe',
                                                        self.channel, 1)

        p.unsubscribe(self.channel)
        assert wait_for_message(p) == self.make_message('unsubscribe',
                                                        self.channel, 0)

    def test_pattern_subscribe_unsubscribe(self, r):
        p = r.pubsub()
        p.psubscribe(self.pattern)
        assert wait_for_message(p) == self.make_message('psubscribe',
                                                        self.pattern, 1)

        p.punsubscribe(self.pattern)
        assert wait_for_message(p) == self.make_message('punsubscribe',
                                                        self.pattern, 0)

    def test_channel_publish(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.subscribe(self.channel)
        r.publish(self.channel, self.data)
        assert wait_for_message(p) == self.make_message('message',
                                                        self.channel,
                                                        self.data)

    def test_pattern_publish(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.psubscribe(self.pattern)
        r.publish(self.channel, self.data)
        assert wait_for_message(p) == self.make_message('pmessage',
                                                        self.channel,
                                                        self.data,
                                                        pattern=self.pattern)

    def test_channel_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.subscribe(**{self.channel: self.message_handler})
        r.publish(self.channel, self.data)
        assert wait_for_message(p) is None
        assert self.message == self.make_message('message', self.channel,
                                                 self.data)

        # test that we reconnected to the correct channel
        p.connection.disconnect()
        assert wait_for_message(p) is None  # should reconnect
        new_data = self.data + u('new data')
        r.publish(self.channel, new_data)
        assert wait_for_message(p) is None
        assert self.message == self.make_message('message', self.channel,
                                                 new_data)

    def test_pattern_message_handler(self, r):
        p = r.pubsub(ignore_subscribe_messages=True)
        p.psubscribe(**{self.pattern: self.message_handler})
        r.publish(self.channel, self.data)
        assert wait_for_message(p) is None
        assert self.message == self.make_message('pmessage', self.channel,
                                                 self.data,
                                                 pattern=self.pattern)

        # test that we reconnected to the correct pattern
        p.connection.disconnect()
        assert wait_for_message(p) is None  # should reconnect
        new_data = self.data + u('new data')
        r.publish(self.channel, new_data)
        assert wait_for_message(p) is None
        assert self.message == self.make_message('pmessage', self.channel,
                                                 new_data,
                                                 pattern=self.pattern)


class TestPubSubRedisDown(object):

    def test_channel_subscribe(self, r):
        r = redis.Redis(host='localhost', port=6390)
        p = r.pubsub()
        with pytest.raises(ConnectionError):
            p.subscribe('foo')
