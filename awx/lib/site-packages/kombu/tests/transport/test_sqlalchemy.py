from __future__ import absolute_import
from __future__ import with_statement

from mock import patch
from nose import SkipTest

from kombu import Connection
from kombu.tests.utils import TestCase


class test_sqlalchemy(TestCase):

    def setUp(self):
        try:
            import sqlalchemy  # noqa
        except ImportError:
            raise SkipTest('sqlalchemy not installed')

    def test_url_parser(self):
        with patch('kombu.transport.sqlalchemy.Channel._open'):
            url = 'sqlalchemy+sqlite:///celerydb.sqlite'
            Connection(url).connect()

            url = 'sqla+sqlite:///celerydb.sqlite'
            Connection(url).connect()

            # Should prevent regression fixed by f187ccd
            url = 'sqlb+sqlite:///celerydb.sqlite'
            with self.assertRaises(KeyError):
                Connection(url).connect()

    def test_clone(self):
        hostname = 'sqlite:///celerydb.sqlite'
        x = Connection('+'.join(['sqla', hostname]))
        self.assertEqual(x.uri_prefix, 'sqla')
        self.assertEqual(x.hostname, hostname)
        clone = x.clone()
        self.assertEqual(clone.hostname, hostname)
        self.assertEqual(clone.uri_prefix, 'sqla')
