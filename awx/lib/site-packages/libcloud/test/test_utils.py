# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one or more§
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import socket
import codecs
import unittest
import warnings
import os.path

from itertools import chain

# In Python > 2.7 DeprecationWarnings are disabled by default
warnings.simplefilter('default')

import libcloud.utils.files

from libcloud.utils.misc import get_driver, set_driver

from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import StringIO
from libcloud.utils.py3 import b
from libcloud.utils.py3 import bchr
from libcloud.utils.py3 import hexadigits
from libcloud.utils.py3 import urlquote
from libcloud.compute.types import Provider
from libcloud.compute.providers import DRIVERS
from libcloud.utils.misc import get_secure_random_string
from libcloud.utils.networking import is_public_subnet
from libcloud.utils.networking import is_private_subnet
from libcloud.utils.networking import is_valid_ip_address
from libcloud.storage.drivers.dummy import DummyIterator


WARNINGS_BUFFER = []

if PY3:
    from io import FileIO as file


def show_warning(msg, cat, fname, lno, line=None):
    WARNINGS_BUFFER.append((msg, cat, fname, lno))

original_func = warnings.showwarning


class TestUtils(unittest.TestCase):
    def setUp(self):
        global WARNINGS_BUFFER
        WARNINGS_BUFFER = []

    def tearDown(self):
        global WARNINGS_BUFFER
        WARNINGS_BUFFER = []
        warnings.showwarning = original_func

    def test_guess_file_mime_type(self):
        file_path = os.path.abspath(__file__)
        mimetype, encoding = libcloud.utils.files.guess_file_mime_type(
            file_path=file_path)

        self.assertTrue(mimetype.find('python') != -1)

    def test_get_driver(self):
        driver = get_driver(drivers=DRIVERS, provider=Provider.DUMMY)
        self.assertTrue(driver is not None)

        try:
            driver = get_driver(drivers=DRIVERS, provider='fooba')
        except AttributeError:
            pass
        else:
            self.fail('Invalid provider, but an exception was not thrown')

    def test_set_driver(self):
        # Set an existing driver
        try:
            driver = set_driver(DRIVERS, Provider.DUMMY,
                                'libcloud.storage.drivers.dummy',
                                'DummyStorageDriver')
        except AttributeError:
            pass

        # Register a new driver
        driver = set_driver(DRIVERS, 'testingset',
                            'libcloud.storage.drivers.dummy',
                            'DummyStorageDriver')

        self.assertTrue(driver is not None)

        # Register it again
        try:
            set_driver(DRIVERS, 'testingset',
                       'libcloud.storage.drivers.dummy',
                       'DummyStorageDriver')
        except AttributeError:
            pass

        # Register an invalid module
        try:
            set_driver(DRIVERS, 'testingnew',
                       'libcloud.storage.drivers.dummy1',
                       'DummyStorageDriver')
        except ImportError:
            pass

        # Register an invalid class
        try:
            set_driver(DRIVERS, 'testingnew',
                       'libcloud.storage.drivers.dummy',
                       'DummyStorageDriver1')
        except AttributeError:
            pass

    def test_deprecated_warning(self):
        warnings.showwarning = show_warning

        libcloud.utils.SHOW_DEPRECATION_WARNING = False
        self.assertEqual(len(WARNINGS_BUFFER), 0)
        libcloud.utils.deprecated_warning('test_module')
        self.assertEqual(len(WARNINGS_BUFFER), 0)

        libcloud.utils.SHOW_DEPRECATION_WARNING = True
        self.assertEqual(len(WARNINGS_BUFFER), 0)
        libcloud.utils.deprecated_warning('test_module')
        self.assertEqual(len(WARNINGS_BUFFER), 1)

    def test_in_development_warning(self):
        warnings.showwarning = show_warning

        libcloud.utils.SHOW_IN_DEVELOPMENT_WARNING = False
        self.assertEqual(len(WARNINGS_BUFFER), 0)
        libcloud.utils.in_development_warning('test_module')
        self.assertEqual(len(WARNINGS_BUFFER), 0)

        libcloud.utils.SHOW_IN_DEVELOPMENT_WARNING = True
        self.assertEqual(len(WARNINGS_BUFFER), 0)
        libcloud.utils.in_development_warning('test_module')
        self.assertEqual(len(WARNINGS_BUFFER), 1)

    def test_read_in_chunks_iterator_no_data(self):
        iterator = DummyIterator()
        generator1 = libcloud.utils.files.read_in_chunks(iterator=iterator,
                                                         yield_empty=False)
        generator2 = libcloud.utils.files.read_in_chunks(iterator=iterator,
                                                         yield_empty=True)

        # yield_empty=False
        count = 0
        for data in generator1:
            count += 1
            self.assertEqual(data, b(''))

        self.assertEqual(count, 0)

        # yield_empty=True
        count = 0
        for data in generator2:
            count += 1
            self.assertEqual(data, b(''))

        self.assertEqual(count, 1)

    def test_read_in_chunks_iterator(self):
        def iterator():
            for x in range(0, 1000):
                yield 'aa'

        for result in libcloud.utils.files.read_in_chunks(iterator(),
                                                          chunk_size=10,
                                                          fill_size=False):
            self.assertEqual(result, b('aa'))

        for result in libcloud.utils.files.read_in_chunks(iterator(), chunk_size=10,
                                                          fill_size=True):
            self.assertEqual(result, b('aaaaaaaaaa'))

    def test_read_in_chunks_filelike(self):
            class FakeFile(file):
                def __init__(self):
                    self.remaining = 500

                def read(self, size):
                    self.remaining -= 1
                    if self.remaining == 0:
                        return ''
                    return 'b' * (size + 1)

            for index, result in enumerate(libcloud.utils.files.read_in_chunks(
                                           FakeFile(), chunk_size=10,
                                           fill_size=False)):
                self.assertEqual(result, b('b' * 11))

            self.assertEqual(index, 498)

            for index, result in enumerate(libcloud.utils.files.read_in_chunks(
                                           FakeFile(), chunk_size=10,
                                           fill_size=True)):
                if index != 548:
                    self.assertEqual(result, b('b' * 10))
                else:
                    self.assertEqual(result, b('b' * 9))

            self.assertEqual(index, 548)

    def test_exhaust_iterator(self):
        def iterator_func():
            for x in range(0, 1000):
                yield 'aa'

        data = b('aa' * 1000)
        iterator = libcloud.utils.files.read_in_chunks(iterator=iterator_func())
        result = libcloud.utils.files.exhaust_iterator(iterator=iterator)
        self.assertEqual(result, data)

        result = libcloud.utils.files.exhaust_iterator(iterator=iterator_func())
        self.assertEqual(result, data)

        data = '12345678990'
        iterator = StringIO(data)
        result = libcloud.utils.files.exhaust_iterator(iterator=iterator)
        self.assertEqual(result, b(data))

    def test_exhaust_iterator_empty_iterator(self):
        data = ''
        iterator = StringIO(data)
        result = libcloud.utils.files.exhaust_iterator(iterator=iterator)
        self.assertEqual(result, b(data))

    def test_unicode_urlquote(self):
        # Regression tests for LIBCLOUD-429
        if PY3:
            # Note: this is a unicode literal
            val = '\xe9'
        else:
            val = codecs.unicode_escape_decode('\xe9')[0]

        uri = urlquote(val)
        self.assertEqual(b(uri), b('%C3%A9'))

        # Unicode without unicode characters
        uri = urlquote('~abc')
        self.assertEqual(b(uri), b('%7Eabc'))

        # Already-encoded bytestring without unicode characters
        uri = urlquote(b('~abc'))
        self.assertEqual(b(uri), b('%7Eabc'))

    def test_get_secure_random_string(self):
        for i in range(1, 500):
            value = get_secure_random_string(size=i)
            self.assertEqual(len(value), i)

    def test_hexadigits(self):
        self.assertEqual(hexadigits(b('')), [])
        self.assertEqual(hexadigits(b('a')), ['61'])
        self.assertEqual(hexadigits(b('AZaz09-')),
                         ['41', '5a', '61', '7a', '30', '39', '2d'])

    def test_bchr(self):
        if PY3:
            self.assertEqual(bchr(0), b'\x00')
            self.assertEqual(bchr(97), b'a')
        else:
            self.assertEqual(bchr(0), '\x00')
            self.assertEqual(bchr(97), 'a')


class NetworkingUtilsTestCase(unittest.TestCase):
    def test_is_public_and_is_private_subnet(self):
        public_ips = [
            '213.151.0.8',
            '86.87.86.1',
            '8.8.8.8',
            '8.8.4.4'
        ]

        private_ips = [
            '192.168.1.100',
            '10.0.0.1',
            '172.16.0.0'
        ]

        for address in public_ips:
            is_public = is_public_subnet(ip=address)
            is_private = is_private_subnet(ip=address)

            self.assertTrue(is_public)
            self.assertFalse(is_private)

        for address in private_ips:
            is_public = is_public_subnet(ip=address)
            is_private = is_private_subnet(ip=address)

            self.assertFalse(is_public)
            self.assertTrue(is_private)

    def test_is_valid_ip_address(self):
        valid_ipv4_addresses = [
            '192.168.1.100',
            '10.0.0.1',
            '213.151.0.8',
            '77.77.77.77'
        ]

        invalid_ipv4_addresses = [
            '10.1',
            '256.256.256.256',
            '0.567.567.567',
            '192.168.0.257'
        ]

        valid_ipv6_addresses = [
            'fe80::200:5aee:feaa:20a2',
            '2607:f0d0:1002:51::4',
            '2607:f0d0:1002:0051:0000:0000:0000:0004',
            '::1'
        ]

        invalid_ipv6_addresses = [
            '2607:f0d',
            '2607:f0d0:0004',
        ]

        for address in valid_ipv4_addresses:
            status = is_valid_ip_address(address=address,
                                         family=socket.AF_INET)
            self.assertTrue(status)

        for address in valid_ipv6_addresses:
            status = is_valid_ip_address(address=address,
                                         family=socket.AF_INET6)
            self.assertTrue(status)

        for address in chain(invalid_ipv4_addresses, invalid_ipv6_addresses):
            status = is_valid_ip_address(address=address,
                                         family=socket.AF_INET)
            self.assertFalse(status)

        for address in chain(invalid_ipv4_addresses, invalid_ipv6_addresses):
            status = is_valid_ip_address(address=address,
                                         family=socket.AF_INET6)
            self.assertFalse(status)


if __name__ == '__main__':
    sys.exit(unittest.main())
