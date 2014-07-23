# Licensed to the Apache Software Foundation (ASF) under one or more
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

import os.path
import sys
import unittest

import libcloud.pricing

PRICING_FILE_PATH = os.path.join(os.path.dirname(__file__), 'pricing_test.json')


class PricingTestCase(unittest.TestCase):

    def test_get_pricing_success(self):
        self.assertFalse('foo' in libcloud.pricing.PRICING_DATA['compute'])

        pricing = libcloud.pricing.get_pricing(driver_type='compute',
                                               driver_name='foo',
                                               pricing_file_path=PRICING_FILE_PATH)
        self.assertEqual(pricing['1'], 1.0)
        self.assertEqual(pricing['2'], 2.0)

        self.assertEqual(libcloud.pricing.PRICING_DATA['compute']['foo']['1'], 1.0)
        self.assertEqual(libcloud.pricing.PRICING_DATA['compute']['foo']['2'], 2.0)

    def test_get_pricing_invalid_file_path(self):
        try:
            libcloud.pricing.get_pricing(driver_type='compute', driver_name='bar',
                                         pricing_file_path='inexistent.json')
        except IOError:
            pass
        else:
            self.fail('Invalid pricing file path provided, but an exception was not'
                      ' thrown')

    def test_get_pricing_invalid_driver_type(self):
        try:
            libcloud.pricing.get_pricing(driver_type='invalid_type', driver_name='bar',
                                         pricing_file_path='inexistent.json')
        except AttributeError:
            pass
        else:
            self.fail('Invalid driver_type provided, but an exception was not'
                      ' thrown')

    def test_get_pricing_not_in_cache(self):
        try:
            libcloud.pricing.get_pricing(driver_type='compute', driver_name='inexistent',
                                         pricing_file_path=PRICING_FILE_PATH)
        except KeyError:
            pass
        else:
            self.fail('Invalid driver provided, but an exception was not'
                      ' thrown')

    def test_get_size_price(self):
        libcloud.pricing.PRICING_DATA['compute']['foo'] = {2: 2, '3': 3}
        price1 = libcloud.pricing.get_size_price(driver_type='compute',
                                                 driver_name='foo',
                                                 size_id=2)
        price2 = libcloud.pricing.get_size_price(driver_type='compute',
                                                 driver_name='foo',
                                                 size_id='3')
        self.assertEqual(price1, 2)
        self.assertEqual(price2, 3)

    def test_invalid_pricing_cache(self):
        libcloud.pricing.PRICING_DATA['compute']['foo'] = {2: 2}
        self.assertTrue('foo' in libcloud.pricing.PRICING_DATA['compute'])

        libcloud.pricing.invalidate_pricing_cache()
        self.assertFalse('foo' in libcloud.pricing.PRICING_DATA['compute'])

    def test_invalid_module_pricing_cache(self):
        libcloud.pricing.PRICING_DATA['compute']['foo'] = {1: 1}

        self.assertTrue('foo' in libcloud.pricing.PRICING_DATA['compute'])

        libcloud.pricing.invalidate_module_pricing_cache(driver_type='compute',
                                                         driver_name='foo')
        self.assertFalse('foo' in libcloud.pricing.PRICING_DATA['compute'])
        libcloud.pricing.invalidate_module_pricing_cache(driver_type='compute',
                                                         driver_name='foo1')

    def test_set_pricing(self):
        self.assertFalse('foo' in libcloud.pricing.PRICING_DATA['compute'])

        libcloud.pricing.set_pricing(driver_type='compute', driver_name='foo',
                                     pricing={'foo': 1})
        self.assertTrue('foo' in libcloud.pricing.PRICING_DATA['compute'])

if __name__ == '__main__':
    sys.exit(unittest.main())
