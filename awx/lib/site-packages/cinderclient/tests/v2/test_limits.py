# Copyright 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from cinderclient.tests import utils
from cinderclient.v2 import limits


def _get_default_RateLimit(verb="verb1", uri="uri1", regex="regex1",
                           value="value1",
                           remain="remain1", unit="unit1",
                           next_available="next1"):
    return limits.RateLimit(verb, uri, regex, value, remain, unit,
                            next_available)


class TestLimits(utils.TestCase):
    def test_repr(self):
        l = limits.Limits(None, {"foo": "bar"})
        self.assertEqual("<Limits>", repr(l))

    def test_absolute(self):
        l = limits.Limits(None,
                          {"absolute": {"name1": "value1", "name2": "value2"}})
        l1 = limits.AbsoluteLimit("name1", "value1")
        l2 = limits.AbsoluteLimit("name2", "value2")
        for item in l.absolute:
            self.assertIn(item, [l1, l2])

    def test_rate(self):
        l = limits.Limits(None,
                          {
                              "rate": [
                                  {
                                      "uri": "uri1",
                                      "regex": "regex1",
                                      "limit": [
                                          {
                                              "verb": "verb1",
                                              "value": "value1",
                                              "remaining": "remain1",
                                              "unit": "unit1",
                                              "next-available": "next1",
                                          },
                                      ],
                                  },
                                  {
                                      "uri": "uri2",
                                      "regex": "regex2",
                                      "limit": [
                                          {
                                              "verb": "verb2",
                                              "value": "value2",
                                              "remaining": "remain2",
                                              "unit": "unit2",
                                              "next-available": "next2",
                                          },
                                      ],
                                  },
                              ],
                          })
        l1 = limits.RateLimit("verb1", "uri1", "regex1", "value1", "remain1",
                              "unit1", "next1")
        l2 = limits.RateLimit("verb2", "uri2", "regex2", "value2", "remain2",
                              "unit2", "next2")
        for item in l.rate:
            self.assertIn(item, [l1, l2])


class TestRateLimit(utils.TestCase):
    def test_equal(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit()
        self.assertEqual(l1, l2)

    def test_not_equal_verbs(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(verb="verb2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_uris(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(uri="uri2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_regexps(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(regex="regex2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_values(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(value="value2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_remains(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(remain="remain2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_units(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(unit="unit2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_next_available(self):
        l1 = _get_default_RateLimit()
        l2 = _get_default_RateLimit(next_available="next2")
        self.assertNotEqual(l1, l2)

    def test_repr(self):
        l1 = _get_default_RateLimit()
        self.assertEqual("<RateLimit: method=verb1 uri=uri1>", repr(l1))


class TestAbsoluteLimit(utils.TestCase):
    def test_equal(self):
        l1 = limits.AbsoluteLimit("name1", "value1")
        l2 = limits.AbsoluteLimit("name1", "value1")
        self.assertEqual(l1, l2)

    def test_not_equal_values(self):
        l1 = limits.AbsoluteLimit("name1", "value1")
        l2 = limits.AbsoluteLimit("name1", "value2")
        self.assertNotEqual(l1, l2)

    def test_not_equal_names(self):
        l1 = limits.AbsoluteLimit("name1", "value1")
        l2 = limits.AbsoluteLimit("name2", "value1")
        self.assertNotEqual(l1, l2)

    def test_repr(self):
        l1 = limits.AbsoluteLimit("name1", "value1")
        self.assertEqual("<AbsoluteLimit: name=name1>", repr(l1))


class TestLimitsManager(utils.TestCase):
    def test_get(self):
        api = mock.Mock()
        api.client.get.return_value = (
            None,
            {"limits": {"absolute": {"name1": "value1", }},
             "no-limits": {"absolute": {"name2": "value2", }}})
        l1 = limits.AbsoluteLimit("name1", "value1")
        limitsManager = limits.LimitsManager(api)

        lim = limitsManager.get()

        self.assertIsInstance(lim, limits.Limits)
        for l in lim.absolute:
            self.assertEqual(l1, l)
