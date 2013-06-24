from __future__ import absolute_import
from __future__ import with_statement

from mock import patch

from kombu import transport

from kombu.tests.utils import TestCase


class test_transport(TestCase):

    def test_resolve_transport_when_callable(self):
        from kombu.transport.memory import Transport
        self.assertIs(transport.resolve_transport(
            'kombu.transport.memory:Transport'),
            Transport)


class test_transport_gettoq(TestCase):

    @patch('warnings.warn')
    def test_compat(self, warn):
        x = transport._ghettoq('Redis', 'redis', 'redis')

        self.assertEqual(x(), 'kombu.transport.redis.Transport')
        self.assertTrue(warn.called)
