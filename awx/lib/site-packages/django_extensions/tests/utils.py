# -*- coding: utf-8 -*-
import sys
import six

from django.test import TestCase
from django.utils.unittest import skipIf

from django_extensions.utils.text import truncate_letters
try:
    import uuid
    assert uuid
except ImportError:
    from django_extensions.utils import uuid


class TruncateLetterTests(TestCase):
    def test_truncate_more_than_text_length(self):
        self.assertEqual(six.u("hello tests"), truncate_letters("hello tests", 100))

    def test_truncate_text(self):
        self.assertEqual(six.u("hello..."), truncate_letters("hello tests", 5))

    def test_truncate_with_range(self):
        for i in range(10, -1, -1):
            self.assertEqual(
                six.u('hello tests'[:i]) + '...',
                truncate_letters("hello tests", i)
            )

    def test_with_non_ascii_characters(self):
        self.assertEqual(
            six.u('\u5ce0 (\u3068\u3046\u3052 t\u014dg...'),
            truncate_letters("峠 (とうげ tōge - mountain pass)", 10)
        )


class UUIDTests(TestCase):
    @skipIf(sys.version_info >= (2, 5, 0), 'uuid already in stdlib')
    def test_uuid3(self):
        # make a UUID using an MD5 hash of a namespace UUID and a name
        self.assertEqual(
            uuid.UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e'),
            uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
        )

    @skipIf(sys.version_info >= (2, 5, 0), 'uuid already in stdlib')
    def test_uuid5(self):
        # make a UUID using a SHA-1 hash of a namespace UUID and a name
        self.assertEqual(
            uuid.UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d'),
            uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
        )

    @skipIf(sys.version_info >= (2, 5, 0), 'uuid already in stdlib')
    def test_uuid_str(self):
        # make a UUID from a string of hex digits (braces and hyphens ignored)
        x = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')
        # convert a UUID to a string of hex digits in standard form
        self.assertEqual('00010203-0405-0607-0809-0a0b0c0d0e0f', str(x))

    @skipIf(sys.version_info >= (2, 5, 0), 'uuid already in stdlib')
    def test_uuid_bytes(self):
        # make a UUID from a string of hex digits (braces and hyphens ignored)
        x = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')
        # get the raw 16 bytes of the UUID
        self.assertEqual(
            '\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f',
            x.bytes
        )

    @skipIf(sys.version_info >= (2, 5, 0), 'uuid already in stdlib')
    def test_make_uuid_from_byte_string(self):
        self.assertEqual(
            uuid.UUID(bytes='\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f'),
            uuid.UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
        )
