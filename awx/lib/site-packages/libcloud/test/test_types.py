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

import sys
import unittest

from libcloud.common.types import LazyList


class TestLazyList(unittest.TestCase):
    def setUp(self):
        super(TestLazyList, self).setUp
        self._get_more_counter = 0

    def tearDown(self):
        super(TestLazyList, self).tearDown

    def test_init(self):
        data = [1, 2, 3, 4, 5]
        ll = LazyList(get_more=self._get_more_exhausted)
        ll_list = list(ll)
        self.assertEqual(ll_list, data)

    def test_iterator(self):
        data = [1, 2, 3, 4, 5]
        ll = LazyList(get_more=self._get_more_exhausted)
        for i, d in enumerate(ll):
            self.assertEqual(d, data[i])

    def test_empty_list(self):
        ll = LazyList(get_more=self._get_more_empty)

        self.assertEqual(list(ll), [])
        self.assertEqual(len(ll), 0)
        self.assertTrue(10 not in ll)

    def test_iterator_not_exhausted(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ll = LazyList(get_more=self._get_more_not_exhausted)
        number_of_iterations = 0
        for i, d in enumerate(ll):
            self.assertEqual(d, data[i])
            number_of_iterations += 1
        self.assertEqual(number_of_iterations, 10)

    def test_len(self):
        ll = LazyList(get_more=self._get_more_not_exhausted)
        ll = LazyList(get_more=self._get_more_not_exhausted)

        self.assertEqual(len(ll), 10)

    def test_contains(self):
        ll = LazyList(get_more=self._get_more_not_exhausted)

        self.assertTrue(40 not in ll)
        self.assertTrue(1 in ll)
        self.assertTrue(5 in ll)
        self.assertTrue(10 in ll)

    def test_indexing(self):
        ll = LazyList(get_more=self._get_more_not_exhausted)

        self.assertEqual(ll[0], 1)
        self.assertEqual(ll[9], 10)
        self.assertEqual(ll[-1], 10)

        try:
            ll[11]
        except IndexError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_repr(self):
        ll1 = LazyList(get_more=self._get_more_empty)
        ll2 = LazyList(get_more=self._get_more_exhausted)
        ll3 = LazyList(get_more=self._get_more_not_exhausted)

        self.assertEqual(repr(ll1), '[]')
        self.assertEqual(repr(ll2), '[1, 2, 3, 4, 5]')
        self.assertEqual(repr(ll3), '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]')

    def _get_more_empty(self, last_key, value_dict):
        return [], None, True

    def _get_more_exhausted(self, last_key, value_dict):
        data = [1, 2, 3, 4, 5]
        return data, 5, True

    def _get_more_not_exhausted(self, last_key, value_dict):
        self._get_more_counter += 1
        if not last_key:
            data, last_key, exhausted = [1, 2, 3, 4, 5], 5, False
        else:
            data, last_key, exhausted = [6, 7, 8, 9, 10], 10, True

        return data, last_key, exhausted

if __name__ == '__main__':
    sys.exit(unittest.main())
