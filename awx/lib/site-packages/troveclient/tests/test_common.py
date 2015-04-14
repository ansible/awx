# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from troveclient import common


class CommonTest(testtools.TestCase):

    def test_check_for_exceptions(self):
        status = [400, 422, 500]
        for s in status:
            resp = mock.Mock()
            resp.status_code = s
            self.assertRaises(Exception,
                              common.check_for_exceptions, resp, "body")

    def test_append_query_strings(self):
        url = "test-url"
        self.assertEqual(url, common.append_query_strings(url))

        self.assertEqual(url, common.append_query_strings(
            url, limit=None, marker=None))

        limit = "test-limit"
        marker = "test-marker"
        result = common.append_query_strings(url, limit=limit, marker=marker)
        self.assertTrue(result.startswith(url + '?'))
        self.assertIn("limit=%s" % limit, result)
        self.assertIn("marker=%s" % marker, result)
        self.assertEqual(1, result.count('&'))

        opts = {}
        self.assertEqual(url, common.append_query_strings(
            url, limit=None, marker=None, **opts))

        opts = {'key1': 'value1', 'key2': None}
        result = common.append_query_strings(url, limit=None, marker=marker,
                                             **opts)
        self.assertTrue(result.startswith(url + '?'))
        self.assertEqual(1, result.count('&'))
        self.assertNotIn("limit=%s" % limit, result)
        self.assertIn("marker=%s" % marker, result)
        self.assertIn("key1=%s" % opts['key1'], result)
        self.assertNotIn("key2=%s" % opts['key2'], result)


class PaginatedTest(testtools.TestCase):

    def setUp(self):
        super(PaginatedTest, self).setUp()
        self.items_ = ["item1", "item2"]
        self.next_marker_ = "next-marker"
        self.links_ = ["link1", "link2"]
        self.pgn = common.Paginated(self.items_, self.next_marker_,
                                    self.links_)

    def tearDown(self):
        super(PaginatedTest, self).tearDown()

    def test___init__(self):
        self.assertEqual(self.items_, self.pgn.items)
        self.assertEqual(self.next_marker_, self.pgn.next)
        self.assertEqual(self.links_, self.pgn.links)

    def test___len__(self):
        self.assertEqual(len(self.items_), self.pgn.__len__())

    def test___iter__(self):
        itr_expected = self.items_.__iter__()
        itr = self.pgn.__iter__()
        self.assertEqual(next(itr_expected), next(itr))
        self.assertEqual(next(itr_expected), next(itr))
        self.assertRaises(StopIteration, next, itr_expected)
        self.assertRaises(StopIteration, next, itr)

    def test___getitem__(self):
        self.assertEqual(self.items_[0], self.pgn.__getitem__(0))

    def test___setitem__(self):
        self.pgn.__setitem__(0, "new-item")
        self.assertEqual("new-item", self.pgn.items[0])

    def test___delitem(self):
        del self.pgn[0]
        self.assertEqual(1, self.pgn.__len__())

    def test___reversed__(self):
        itr = self.pgn.__reversed__()
        self.assertEqual("item2", next(itr))
        self.assertEqual("item1", next(itr))
        self.assertRaises(StopIteration, next, itr)

    def test___contains__(self):
        self.assertTrue(self.pgn.__contains__("item1"))
        self.assertTrue(self.pgn.__contains__("item2"))
        self.assertFalse(self.pgn.__contains__("item3"))
