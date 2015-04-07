# Copyright 2013 Mirantis, Inc.
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

from oslo_config import types


class TypeTestHelper(object):
    def setUp(self):
        super(TypeTestHelper, self).setUp()
        self.type_instance = self.type

    def assertConvertedValue(self, s, expected):
        self.assertEqual(expected, self.type_instance(s))

    def assertInvalid(self, value):
        self.assertRaises(ValueError, self.type_instance, value)


class StringTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.String()

    def test_empty_string_passes(self):
        self.assertConvertedValue('', '')

    def test_should_return_same_string_if_valid(self):
        self.assertConvertedValue('foo bar', 'foo bar')

    def test_listed_value(self):
        self.type_instance = types.String(choices=['foo', 'bar'])
        self.assertConvertedValue('foo', 'foo')

    def test_unlisted_value(self):
        self.type_instance = types.String(choices=['foo', 'bar'])
        self.assertInvalid('baz')

    def test_with_no_values_returns_error(self):
        self.type_instance = types.String(choices=[])
        self.assertInvalid('foo')

    def test_string_with_non_closed_quote_is_invalid(self):
        self.type_instance = types.String(quotes=True)
        self.assertInvalid('"foo bar')
        self.assertInvalid("'bar baz")

    def test_quotes_are_stripped(self):
        self.type_instance = types.String(quotes=True)
        self.assertConvertedValue('"foo bar"', 'foo bar')

    def test_trailing_quote_is_ok(self):
        self.type_instance = types.String(quotes=True)
        self.assertConvertedValue('foo bar"', 'foo bar"')

    def test_repr(self):
        t = types.String()
        self.assertEqual('String', repr(t))

    def test_repr_with_choices(self):
        t = types.String(choices=['foo', 'bar'])
        self.assertEqual('String(choices=[\'foo\', \'bar\'])', repr(t))

    def test_equal(self):
        self.assertTrue(types.String() == types.String())

    def test_equal_with_same_choices(self):
        t1 = types.String(choices=['foo', 'bar'])
        t2 = types.String(choices=['foo', 'bar'])
        self.assertTrue(t1 == t2)

    def test_not_equal_with_different_choices(self):
        t1 = types.String(choices=['foo', 'bar'])
        t2 = types.String(choices=['foo', 'baz'])
        self.assertFalse(t1 == t2)

    def test_equal_with_equal_quote_falgs(self):
        t1 = types.String(quotes=True)
        t2 = types.String(quotes=True)
        self.assertTrue(t1 == t2)

    def test_not_equal_with_different_quote_falgs(self):
        t1 = types.String(quotes=False)
        t2 = types.String(quotes=True)
        self.assertFalse(t1 == t2)

    def test_not_equal_to_other_class(self):
        self.assertFalse(types.String() == types.Integer())


class BooleanTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.Boolean()

    def test_True(self):
        self.assertConvertedValue('True', True)

    def test_yes(self):
        self.assertConvertedValue('yes', True)

    def test_on(self):
        self.assertConvertedValue('on', True)

    def test_1(self):
        self.assertConvertedValue('1', True)

    def test_False(self):
        self.assertConvertedValue('False', False)

    def test_no(self):
        self.assertConvertedValue('no', False)

    def test_off(self):
        self.assertConvertedValue('off', False)

    def test_0(self):
        self.assertConvertedValue('0', False)

    def test_other_values_produce_error(self):
        self.assertInvalid('foo')

    def test_repr(self):
        self.assertEqual('Boolean', repr(types.Boolean()))

    def test_equal(self):
        self.assertEqual(types.Boolean(), types.Boolean())

    def test_not_equal_to_other_class(self):
        self.assertFalse(types.Boolean() == types.String())


class IntegerTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.Integer()

    def test_empty_string(self):
        self.assertConvertedValue('', None)

    def test_whitespace_string(self):
        self.assertConvertedValue("   \t\t\t\t", None)

    def test_positive_values_are_valid(self):
        self.assertConvertedValue('123', 123)

    def test_zero_is_valid(self):
        self.assertConvertedValue('0', 0)

    def test_negative_values_are_valid(self):
        self.assertConvertedValue('-123', -123)

    def test_leading_whitespace_is_ignored(self):
        self.assertConvertedValue('   5', 5)

    def test_trailing_whitespace_is_ignored(self):
        self.assertConvertedValue('7   ', 7)

    def test_non_digits_are_invalid(self):
        self.assertInvalid('12a45')

    def test_repr(self):
        t = types.Integer()
        self.assertEqual('Integer', repr(t))

    def test_repr_with_min(self):
        t = types.Integer(min=123)
        self.assertEqual('Integer(min=123)', repr(t))

    def test_repr_with_max(self):
        t = types.Integer(max=456)
        self.assertEqual('Integer(max=456)', repr(t))

    def test_repr_with_min_and_max(self):
        t = types.Integer(min=123, max=456)
        self.assertEqual('Integer(min=123, max=456)', repr(t))

    def test_equal(self):
        self.assertTrue(types.Integer() == types.Integer())

    def test_equal_with_same_min_and_no_max(self):
        self.assertTrue(types.Integer(min=123) == types.Integer(min=123))

    def test_equal_with_same_max_and_no_min(self):
        self.assertTrue(types.Integer(max=123) == types.Integer(max=123))

    def test_equal_with_same_min_and_max(self):
        t1 = types.Integer(min=1, max=123)
        t2 = types.Integer(min=1, max=123)
        self.assertTrue(t1 == t2)

    def test_not_equal(self):
        self.assertFalse(types.Integer(min=123) == types.Integer(min=456))

    def test_not_equal_to_other_class(self):
        self.assertFalse(types.Integer() == types.String())

    def test_with_max_and_min(self):
        t = types.Integer(min=123, max=456)
        self.assertRaises(ValueError, t, 122)
        t(123)
        t(300)
        t(456)
        self.assertRaises(ValueError, t, 0)
        self.assertRaises(ValueError, t, 457)


class FloatTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.Float()

    def test_decimal_format(self):
        v = self.type_instance('123.456')
        self.assertAlmostEqual(v, 123.456)

    def test_decimal_format_negative_float(self):
        v = self.type_instance('-123.456')
        self.assertAlmostEqual(v, -123.456)

    def test_exponential_format(self):
        v = self.type_instance('123e-2')
        self.assertAlmostEqual(v, 1.23)

    def test_non_float_is_invalid(self):
        self.assertInvalid('123,345')
        self.assertInvalid('foo')

    def test_repr(self):
        self.assertEqual('Float', repr(types.Float()))

    def test_equal(self):
        self.assertTrue(types.Float() == types.Float())

    def test_not_equal_to_other_class(self):
        self.assertFalse(types.Float() == types.Integer())


class ListTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.List()

    def test_empty_value(self):
        self.assertConvertedValue('', [])

    def test_single_value(self):
        self.assertConvertedValue(' foo bar ',
                                  ['foo bar'])

    def test_list_of_values(self):
        self.assertConvertedValue(' foo bar, baz ',
                                  ['foo bar',
                                   'baz'])

    def test_list_of_values_containing_commas(self):
        self.type_instance = types.List(types.String(quotes=True))
        self.assertConvertedValue('foo,"bar, baz",bam',
                                  ['foo',
                                   'bar, baz',
                                   'bam'])

    def test_list_of_lists(self):
        self.type_instance = types.List(
            types.List(types.String(), bounds=True)
        )
        self.assertConvertedValue('[foo],[bar, baz],[bam]',
                                  [['foo'], ['bar', 'baz'], ['bam']])

    def test_list_of_custom_type(self):
        self.type_instance = types.List(types.Integer())
        self.assertConvertedValue('1,2,3,5',
                                  [1, 2, 3, 5])

    def test_bounds_parsing(self):
        self.type_instance = types.List(types.Integer(), bounds=True)
        self.assertConvertedValue('[1,2,3]', [1, 2, 3])

    def test_bounds_required(self):
        self.type_instance = types.List(types.Integer(), bounds=True)
        self.assertInvalid('1,2,3')
        self.assertInvalid('[1,2,3')
        self.assertInvalid('1,2,3]')

    def test_repr(self):
        t = types.List(types.Integer())
        self.assertEqual('List of Integer', repr(t))

    def test_equal(self):
        self.assertTrue(types.List() == types.List())

    def test_equal_with_equal_custom_item_types(self):
        it1 = types.Integer()
        it2 = types.Integer()
        self.assertTrue(types.List(it1) == types.List(it2))

    def test_not_equal_with_non_equal_custom_item_types(self):
        it1 = types.Integer()
        it2 = types.String()
        self.assertFalse(it1 == it2)
        self.assertFalse(types.List(it1) == types.List(it2))

    def test_not_equal_to_other_class(self):
        self.assertFalse(types.List() == types.Integer())


class DictTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.Dict()

    def test_empty_value(self):
        self.assertConvertedValue('', {})

    def test_single_value(self):
        self.assertConvertedValue(' foo: bar ',
                                  {'foo': 'bar'})

    def test_dict_of_values(self):
        self.assertConvertedValue(' foo: bar, baz: 123 ',
                                  {'foo': 'bar',
                                   'baz': '123'})

    def test_custom_value_type(self):
        self.type_instance = types.Dict(types.Integer())
        self.assertConvertedValue('foo:123, bar: 456',
                                  {'foo': 123,
                                   'bar': 456})

    def test_dict_of_values_containing_commas(self):
        self.type_instance = types.Dict(types.String(quotes=True))
        self.assertConvertedValue('foo:"bar, baz",bam:quux',
                                  {'foo': 'bar, baz',
                                   'bam': 'quux'})

    def test_dict_of_dicts(self):
        self.type_instance = types.Dict(
            types.Dict(types.String(), bounds=True)
        )
        self.assertConvertedValue('k1:{k1:v1,k2:v2},k2:{k3:v3}',
                                  {'k1': {'k1': 'v1', 'k2': 'v2'},
                                   'k2': {'k3': 'v3'}})

    def test_bounds_parsing(self):
        self.type_instance = types.Dict(types.String(), bounds=True)
        self.assertConvertedValue('{foo:bar,baz:123}',
                                  {'foo': 'bar',
                                   'baz': '123'})

    def test_bounds_required(self):
        self.type_instance = types.Dict(types.String(), bounds=True)
        self.assertInvalid('foo:bar,baz:123')
        self.assertInvalid('{foo:bar,baz:123')
        self.assertInvalid('foo:bar,baz:123}')

    def test_no_mapping_produces_error(self):
        self.assertInvalid('foo,bar')

    def test_repr(self):
        t = types.Dict(types.Integer())
        self.assertEqual('Dict of Integer', repr(t))

    def test_equal(self):
        self.assertTrue(types.Dict() == types.Dict())

    def test_equal_with_equal_custom_item_types(self):
        it1 = types.Integer()
        it2 = types.Integer()
        self.assertTrue(types.Dict(it1) == types.Dict(it2))

    def test_not_equal_with_non_equal_custom_item_types(self):
        it1 = types.Integer()
        it2 = types.String()
        self.assertFalse(it1 == it2)
        self.assertFalse(types.Dict(it1) == types.Dict(it2))

    def test_not_equal_to_other_class(self):
        self.assertFalse(types.Dict() == types.Integer())


class IPAddressTypeTests(TypeTestHelper, unittest.TestCase):
    type = types.IPAddress()

    def test_ipv4_address(self):
        self.assertConvertedValue('192.168.0.1', '192.168.0.1')

    def test_ipv6_address(self):
        self.assertConvertedValue('abcd:ef::1', 'abcd:ef::1')

    def test_strings(self):
        self.assertInvalid('')
        self.assertInvalid('foo')

    def test_numbers(self):
        self.assertInvalid(1)
        self.assertInvalid(-1)
        self.assertInvalid(3.14)


class IPv4AddressTypeTests(IPAddressTypeTests):
    type = types.IPAddress(4)

    def test_ipv6_address(self):
        self.assertInvalid('abcd:ef::1')


class IPv6AddressTypeTests(IPAddressTypeTests):
    type = types.IPAddress(6)

    def test_ipv4_address(self):
        self.assertInvalid('192.168.0.1')
