#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import with_statement

import sys

from base64 import b64decode

from kombu.serialization import (registry, register, SerializerNotInstalled,
                                 raw_encode, register_yaml, register_msgpack,
                                 decode, bytes_t, pickle, pickle_protocol,
                                 unregister, register_pickle)

from .utils import TestCase
from .utils import mask_modules, skip_if_not_module

# For content_encoding tests
unicode_string = u'abcdé\u8463'
unicode_string_as_utf8 = unicode_string.encode('utf-8')
latin_string = u'abcdé'
latin_string_as_latin1 = latin_string.encode('latin-1')
latin_string_as_utf8 = latin_string.encode('utf-8')


# For serialization tests
py_data = {
    'string': 'The quick brown fox jumps over the lazy dog',
    'int': 10,
    'float': 3.14159265,
    'unicode': u'Thé quick brown fox jumps over thé lazy dog',
    'list': ['george', 'jerry', 'elaine', 'cosmo'],
}

# JSON serialization tests
json_data = """\
{"int": 10, "float": 3.1415926500000002, \
"list": ["george", "jerry", "elaine", "cosmo"], \
"string": "The quick brown fox jumps over the lazy \
dog", "unicode": "Th\\u00e9 quick brown fox jumps over \
th\\u00e9 lazy dog"}\
"""

# Pickle serialization tests
pickle_data = pickle.dumps(py_data, protocol=pickle_protocol)

# YAML serialization tests
yaml_data = """\
float: 3.1415926500000002
int: 10
list: [george, jerry, elaine, cosmo]
string: The quick brown fox jumps over the lazy dog
unicode: "Th\\xE9 quick brown fox jumps over th\\xE9 lazy dog"
"""


msgpack_py_data = dict(py_data)
# Unicode chars are lost in transmit :(
msgpack_py_data['unicode'] = 'Th quick brown fox jumps over th lazy dog'
msgpack_data = b64decode("""\
haNpbnQKpWZsb2F0y0AJIftTyNTxpGxpc3SUpmdlb3JnZaVqZXJyeaZlbGFpbmWlY29zbW+mc3Rya\
W5n2gArVGhlIHF1aWNrIGJyb3duIGZveCBqdW1wcyBvdmVyIHRoZSBsYXp5IGRvZ6d1bmljb2Rl2g\
ApVGggcXVpY2sgYnJvd24gZm94IGp1bXBzIG92ZXIgdGggbGF6eSBkb2c=\
""")


def say(m):
    sys.stderr.write('%s\n' % (m, ))


registry.register('testS', lambda s: s, lambda s: 'decoded',
                  'application/testS', 'utf-8')


class test_Serialization(TestCase):

    def test_disable(self):
        disabled = registry._disabled_content_types
        try:
            registry.disable('testS')
            self.assertIn('application/testS', disabled)
            disabled.clear()

            registry.disable('application/testS')
            self.assertIn('application/testS', disabled)
        finally:
            disabled.clear()

    def test_decode_when_disabled(self):
        disabled = registry._disabled_content_types
        try:
            registry.disable('testS')

            with self.assertRaises(SerializerNotInstalled):
                registry.decode(
                    'xxd', 'application/testS', 'utf-8', force=False,
                )

            ret = registry.decode(
                'xxd', 'application/testS', 'utf-8', force=True,
            )
            self.assertEqual(ret, 'decoded')
        finally:
            disabled.clear()

    def test_decode_when_data_is_None(self):
        registry.decode(None, 'application/testS', 'utf-8')

    def test_content_type_decoding(self):
        self.assertEqual(
            unicode_string,
            registry.decode(unicode_string_as_utf8,
                            content_type='plain/text',
                            content_encoding='utf-8'),
        )
        self.assertEqual(
            latin_string,
            registry.decode(latin_string_as_latin1,
                            content_type='application/data',
                            content_encoding='latin-1'),
        )

    def test_content_type_binary(self):
        self.assertIsInstance(
            registry.decode(unicode_string_as_utf8,
                            content_type='application/data',
                            content_encoding='binary'),
            bytes_t,
        )

        self.assertEqual(
            unicode_string_as_utf8,
            registry.decode(unicode_string_as_utf8,
                            content_type='application/data',
                            content_encoding='binary'),
        )

    def test_content_type_encoding(self):
        # Using the 'raw' serializer
        self.assertEqual(
            unicode_string_as_utf8,
            registry.encode(unicode_string, serializer='raw')[-1],
        )
        self.assertEqual(
            latin_string_as_utf8,
            registry.encode(latin_string, serializer='raw')[-1],
        )
        # And again w/o a specific serializer to check the
        # code where we force unicode objects into a string.
        self.assertEqual(
            unicode_string_as_utf8,
            registry.encode(unicode_string)[-1],
        )
        self.assertEqual(
            latin_string_as_utf8,
            registry.encode(latin_string)[-1],
        )

    def test_json_decode(self):
        self.assertEqual(
            py_data,
            registry.decode(json_data,
                            content_type='application/json',
                            content_encoding='utf-8'),
        )

    def test_json_encode(self):
        self.assertEqual(
            registry.decode(
                registry.encode(py_data, serializer='json')[-1],
                content_type='application/json',
                content_encoding='utf-8',
            ),
            registry.decode(
                json_data,
                content_type='application/json',
                content_encoding='utf-8',
            ),
        )

    @skip_if_not_module('msgpack')
    def test_msgpack_decode(self):
        register_msgpack()
        self.assertEqual(
            msgpack_py_data,
            registry.decode(msgpack_data,
                            content_type='application/x-msgpack',
                            content_encoding='binary'),
        )

    @skip_if_not_module('msgpack')
    def test_msgpack_encode(self):
        register_msgpack()
        self.assertEqual(
            registry.decode(
                registry.encode(msgpack_py_data, serializer='msgpack')[-1],
                content_type='application/x-msgpack',
                content_encoding='binary',
            ),
            registry.decode(
                msgpack_data,
                content_type='application/x-msgpack',
                content_encoding='binary',
            ),
        )

    @skip_if_not_module('yaml')
    def test_yaml_decode(self):
        register_yaml()
        self.assertEqual(
            py_data,
            registry.decode(yaml_data,
                            content_type='application/x-yaml',
                            content_encoding='utf-8'),
        )

    @skip_if_not_module('yaml')
    def test_yaml_encode(self):
        register_yaml()
        self.assertEqual(
            registry.decode(
                registry.encode(py_data, serializer='yaml')[-1],
                content_type='application/x-yaml',
                content_encoding='utf-8',
            ),
            registry.decode(
                yaml_data,
                content_type='application/x-yaml',
                content_encoding='utf-8',
            ),
        )

    def test_pickle_decode(self):
        self.assertEqual(
            py_data,
            registry.decode(pickle_data,
                            content_type='application/x-python-serialize',
                            content_encoding='binary'),
        )

    def test_pickle_encode(self):
        self.assertEqual(
            pickle.loads(pickle_data),
            pickle.loads(registry.encode(py_data, serializer='pickle')[-1]),
        )

    def test_register(self):
        register(None, None, None, None)

    def test_unregister(self):
        with self.assertRaises(SerializerNotInstalled):
            unregister('nonexisting')
        registry.encode('foo', serializer='pickle')
        unregister('pickle')
        with self.assertRaises(SerializerNotInstalled):
            registry.encode('foo', serializer='pickle')
        register_pickle()

    def test_set_default_serializer_missing(self):
        with self.assertRaises(SerializerNotInstalled):
            registry._set_default_serializer('nonexisting')

    def test_encode_missing(self):
        with self.assertRaises(SerializerNotInstalled):
            registry.encode('foo', serializer='nonexisting')

    def test_raw_encode(self):
        self.assertTupleEqual(
            raw_encode('foo'.encode('utf-8')),
            ('application/data', 'binary', 'foo'.encode('utf-8')),
        )

    @mask_modules('yaml')
    def test_register_yaml__no_yaml(self):
        register_yaml()
        with self.assertRaises(SerializerNotInstalled):
            decode('foo', 'application/x-yaml', 'utf-8')

    @mask_modules('msgpack')
    def test_register_msgpack__no_msgpack(self):
        register_msgpack()
        with self.assertRaises(SerializerNotInstalled):
            decode('foo', 'application/x-msgpack', 'utf-8')
