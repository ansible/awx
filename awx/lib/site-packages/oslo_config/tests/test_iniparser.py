# Copyright 2012 OpenStack Foundation
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

import unittest

from oslo_config import iniparser


class TestParser(iniparser.BaseParser):
    comment_called = False
    values = None
    section = ''

    def __init__(self):
        self.values = {}

    def assignment(self, key, value):
        self.values.setdefault(self.section, {})
        self.values[self.section][key] = value

    def new_section(self, section):
        self.section = section

    def comment(self, section):
        self.comment_called = True


class BaseParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = iniparser.BaseParser()

    def _assertParseError(self, *lines):
        self.assertRaises(iniparser.ParseError, self.parser.parse, lines)

    def test_invalid_assignment(self):
        self._assertParseError("foo - bar")

    def test_empty_key(self):
        self._assertParseError(": bar")

    def test_unexpected_continuation(self):
        self._assertParseError("   baz")

    def test_invalid_section(self):
        self._assertParseError("[section")

    def test_no_section_name(self):
        self._assertParseError("[]")


class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = TestParser()

    def test_blank_line(self):
        lines = [""]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {})

    def test_assignment_equal(self):
        lines = ["foo = bar"]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'': {'foo': ['bar']}})

    def test_assignment_colon(self):
        lines = ["foo: bar"]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'': {'foo': ['bar']}})

    def test_assignment_multiline(self):
        lines = ["foo = bar0", "  bar1"]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'': {'foo': ['bar0', 'bar1']}})

    def test_assignment_multline_empty(self):
        lines = ["foo = bar0", "", "  bar1"]
        self.assertRaises(iniparser.ParseError, self.parser.parse, lines)

    def test_section_assignment(self):
        lines = ["[test]", "foo = bar"]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'test': {'foo': ['bar']}})

    def test_new_section(self):
        lines = ["[foo]"]
        self.parser.parse(lines)
        self.assertEqual(self.parser.section, 'foo')

    def test_comment(self):
        lines = ["# foobar"]
        self.parser.parse(lines)
        self.assertTrue(self.parser.comment_called)

    def test_empty_assignment(self):
        lines = ["foo = "]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'': {'foo': ['']}})

    def test_assignment_space_single_quote(self):
        lines = ["foo = ' bar '"]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'': {'foo': [' bar ']}})

    def test_assignment_space_double_quote(self):
        lines = ["foo = \" bar \""]
        self.parser.parse(lines)
        self.assertEqual(self.parser.values, {'': {'foo': [' bar ']}})


class ExceptionTestCase(unittest.TestCase):
    def test_parseerror(self):
        exc = iniparser.ParseError('test', 42, 'example')
        self.assertEqual(str(exc), "at line 42, test: 'example'")
