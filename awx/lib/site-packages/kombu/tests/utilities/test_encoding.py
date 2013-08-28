# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import with_statement

import sys

from contextlib import contextmanager
from mock import patch
from nose import SkipTest

from kombu.utils.encoding import bytes_t, safe_str, default_encoding

from kombu.tests.utils import TestCase


@contextmanager
def clean_encoding():
    old_encoding = sys.modules.pop('kombu.utils.encoding', None)
    import kombu.utils.encoding
    try:
        yield kombu.utils.encoding
    finally:
        if old_encoding:
            sys.modules['kombu.utils.encoding'] = old_encoding


class test_default_encoding(TestCase):

    @patch('sys.getdefaultencoding')
    def test_default(self, getdefaultencoding):
        getdefaultencoding.return_value = 'ascii'
        with clean_encoding() as encoding:
            enc = encoding.default_encoding()
            if sys.platform.startswith('java'):
                self.assertEqual(enc, 'utf-8')
            else:
                self.assertEqual(enc, 'ascii')
                getdefaultencoding.assert_called_with()


class test_encoding_utils(TestCase):

    def setUp(self):
        if sys.version_info >= (3, 0):
            raise SkipTest('not relevant on py3k')

    def test_str_to_bytes(self):
        with clean_encoding() as e:
            self.assertIsInstance(e.str_to_bytes(u'foobar'), str)
            self.assertIsInstance(e.str_to_bytes('foobar'), str)

    def test_from_utf8(self):
        with clean_encoding() as e:
            self.assertIsInstance(e.from_utf8(u'foobar'), str)

    def test_default_encode(self):
        with clean_encoding() as e:
            self.assertTrue(e.default_encode('foo'))


class test_safe_str(TestCase):

    def setUp(self):
        self._cencoding = patch('sys.getdefaultencoding')
        self._encoding = self._cencoding.__enter__()
        self._encoding.return_value = 'ascii'

    def tearDown(self):
        self._cencoding.__exit__()

    def test_when_bytes(self):
        self.assertEqual(safe_str('foo'), 'foo')

    def test_when_unicode(self):
        self.assertIsInstance(safe_str(u'foo'), bytes_t)

    def test_when_encoding_utf8(self):
        with patch('sys.getdefaultencoding') as encoding:
            encoding.return_value = 'utf-8'
            self.assertEqual(default_encoding(), 'utf-8')
            s = u'The quiæk fåx jømps øver the lazy dåg'
            res = safe_str(s)
            self.assertIsInstance(res, bytes_t)
            self.assertGreater(len(res), len(s))

    def test_when_containing_high_chars(self):
        with patch('sys.getdefaultencoding') as encoding:
            encoding.return_value = 'ascii'
            s = u'The quiæk fåx jømps øver the lazy dåg'
            res = safe_str(s)
            self.assertIsInstance(res, bytes_t)
            self.assertEqual(len(s), len(res))

    def test_when_not_string(self):
        o = object()
        self.assertEqual(safe_str(o), repr(o))

    def test_when_unrepresentable(self):

        class O(object):

            def __repr__(self):
                raise KeyError('foo')

        self.assertIn('<Unrepresentable', safe_str(O()))
