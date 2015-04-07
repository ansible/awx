# Copyright 2011 OpenStack Foundation.
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

import collections
import datetime
import json

import mock
import netaddr
from oslo_i18n import fixture
from oslotest import base as test_base
import simplejson
import six
import six.moves.xmlrpc_client as xmlrpclib

from oslo_serialization import jsonutils


class JSONUtilsTestMixin(object):

    json_impl = None

    def setUp(self):
        super(JSONUtilsTestMixin, self).setUp()
        self.json_patcher = mock.patch.multiple(
            jsonutils, json=self.json_impl,
            is_simplejson=self.json_impl is simplejson)
        self.json_impl_mock = self.json_patcher.start()

    def tearDown(self):
        self.json_patcher.stop()
        super(JSONUtilsTestMixin, self).tearDown()

    def test_dumps(self):
        self.assertEqual('{"a": "b"}', jsonutils.dumps({'a': 'b'}))

    def test_dumps_namedtuple(self):
        n = collections.namedtuple("foo", "bar baz")(1, 2)
        self.assertEqual('[1, 2]', jsonutils.dumps(n))

    def test_dump(self):
        expected = '{"a": "b"}'
        json_dict = {'a': 'b'}

        fp = six.StringIO()
        jsonutils.dump(json_dict, fp)

        self.assertEqual(expected, fp.getvalue())

    def test_dump_namedtuple(self):
        expected = '[1, 2]'
        json_dict = collections.namedtuple("foo", "bar baz")(1, 2)

        fp = six.StringIO()
        jsonutils.dump(json_dict, fp)

        self.assertEqual(expected, fp.getvalue())

    def test_loads(self):
        self.assertEqual({'a': 'b'}, jsonutils.loads('{"a": "b"}'))

    def test_loads_unicode(self):
        self.assertIsInstance(jsonutils.loads(b'"foo"'), six.text_type)
        self.assertIsInstance(jsonutils.loads(u'"foo"'), six.text_type)

        # 'test' in Ukrainian
        i18n_str_unicode = u'"\u0442\u0435\u0441\u0442"'
        self.assertIsInstance(jsonutils.loads(i18n_str_unicode), six.text_type)

        i18n_str = i18n_str_unicode.encode('utf-8')
        self.assertIsInstance(jsonutils.loads(i18n_str), six.text_type)

    def test_loads_with_kwargs(self):
        jsontext = u'{"foo": 3}'
        result = jsonutils.loads(jsontext, parse_int=lambda x: 5)
        self.assertEqual(5, result['foo'])

    def test_load(self):

        jsontext = u'{"a": "\u0442\u044d\u0441\u0442"}'
        expected = {u'a': u'\u0442\u044d\u0441\u0442'}

        for encoding in ('utf-8', 'cp1251'):
            fp = six.BytesIO(jsontext.encode(encoding))
            result = jsonutils.load(fp, encoding=encoding)
            self.assertEqual(expected, result)
            for key, val in result.items():
                self.assertIsInstance(key, six.text_type)
                self.assertIsInstance(val, six.text_type)


class JSONUtilsTestJson(JSONUtilsTestMixin, test_base.BaseTestCase):
    json_impl = json


class JSONUtilsTestSimpleJson(JSONUtilsTestMixin, test_base.BaseTestCase):
    json_impl = simplejson


class ToPrimitiveTestCase(test_base.BaseTestCase):
    def setUp(self):
        super(ToPrimitiveTestCase, self).setUp()
        self.trans_fixture = self.useFixture(fixture.Translation())

    def test_list(self):
        self.assertEqual(jsonutils.to_primitive([1, 2, 3]), [1, 2, 3])

    def test_empty_list(self):
        self.assertEqual(jsonutils.to_primitive([]), [])

    def test_tuple(self):
        self.assertEqual(jsonutils.to_primitive((1, 2, 3)), [1, 2, 3])

    def test_dict(self):
        self.assertEqual(jsonutils.to_primitive(dict(a=1, b=2, c=3)),
                         dict(a=1, b=2, c=3))

    def test_empty_dict(self):
        self.assertEqual(jsonutils.to_primitive({}), {})

    def test_datetime(self):
        x = datetime.datetime(1920, 2, 3, 4, 5, 6, 7)
        self.assertEqual(jsonutils.to_primitive(x),
                         '1920-02-03T04:05:06.000007')

    def test_datetime_preserve(self):
        x = datetime.datetime(1920, 2, 3, 4, 5, 6, 7)
        self.assertEqual(jsonutils.to_primitive(x, convert_datetime=False), x)

    def test_DateTime(self):
        x = xmlrpclib.DateTime()
        x.decode("19710203T04:05:06")
        self.assertEqual(jsonutils.to_primitive(x),
                         '1971-02-03T04:05:06.000000')

    def test_iter(self):
        class IterClass(object):
            def __init__(self):
                self.data = [1, 2, 3, 4, 5]
                self.index = 0

            def __iter__(self):
                return self

            def next(self):
                if self.index == len(self.data):
                    raise StopIteration
                self.index = self.index + 1
                return self.data[self.index - 1]
            __next__ = next

        x = IterClass()
        self.assertEqual(jsonutils.to_primitive(x), [1, 2, 3, 4, 5])

    def test_iteritems(self):
        class IterItemsClass(object):
            def __init__(self):
                self.data = dict(a=1, b=2, c=3).items()
                self.index = 0

            def iteritems(self):
                return self.data

        x = IterItemsClass()
        p = jsonutils.to_primitive(x)
        self.assertEqual(p, {'a': 1, 'b': 2, 'c': 3})

    def test_iteritems_with_cycle(self):
        class IterItemsClass(object):
            def __init__(self):
                self.data = dict(a=1, b=2, c=3)
                self.index = 0

            def iteritems(self):
                return self.data.items()

        x = IterItemsClass()
        x2 = IterItemsClass()
        x.data['other'] = x2
        x2.data['other'] = x

        # If the cycle isn't caught, to_primitive() will eventually result in
        # an exception due to excessive recursion depth.
        jsonutils.to_primitive(x)

    def test_instance(self):
        class MysteryClass(object):
            a = 10

            def __init__(self):
                self.b = 1

        x = MysteryClass()
        self.assertEqual(jsonutils.to_primitive(x, convert_instances=True),
                         dict(b=1))

        self.assertEqual(jsonutils.to_primitive(x), x)

    def test_typeerror(self):
        x = bytearray  # Class, not instance
        if six.PY3:
            self.assertEqual(jsonutils.to_primitive(x), u"<class 'bytearray'>")
        else:
            self.assertEqual(jsonutils.to_primitive(x), u"<type 'bytearray'>")

    def test_nasties(self):
        def foo():
            pass
        x = [datetime, foo, dir]
        ret = jsonutils.to_primitive(x)
        self.assertEqual(len(ret), 3)
        self.assertTrue(ret[0].startswith(u"<module 'datetime' from ") or
                        ret[0].startswith(u"<module 'datetime' (built-in)"))
        if six.PY3:
            self.assertTrue(ret[1].startswith(
                '<function ToPrimitiveTestCase.test_nasties.<locals>.foo at 0x'
            ))
        else:
            self.assertTrue(ret[1].startswith('<function foo at 0x'))
        self.assertEqual(ret[2], '<built-in function dir>')

    def test_depth(self):
        class LevelsGenerator(object):
            def __init__(self, levels):
                self._levels = levels

            def iteritems(self):
                if self._levels == 0:
                    return iter([])
                else:
                    return iter([(0, LevelsGenerator(self._levels - 1))])

        l4_obj = LevelsGenerator(4)

        json_l2 = {0: {0: '?'}}
        json_l3 = {0: {0: {0: '?'}}}
        json_l4 = {0: {0: {0: {0: '?'}}}}

        ret = jsonutils.to_primitive(l4_obj, max_depth=2)
        self.assertEqual(ret, json_l2)

        ret = jsonutils.to_primitive(l4_obj, max_depth=3)
        self.assertEqual(ret, json_l3)

        ret = jsonutils.to_primitive(l4_obj, max_depth=4)
        self.assertEqual(ret, json_l4)

    def test_ipaddr(self):
        thing = {'ip_addr': netaddr.IPAddress('1.2.3.4')}
        ret = jsonutils.to_primitive(thing)
        self.assertEqual({'ip_addr': '1.2.3.4'}, ret)

    def test_message_with_param(self):
        msg = self.trans_fixture.lazy('A message with param: %s')
        msg = msg % 'test_domain'
        ret = jsonutils.to_primitive(msg)
        self.assertEqual(msg, ret)

    def test_message_with_named_param(self):
        msg = self.trans_fixture.lazy('A message with params: %(param)s')
        msg = msg % {'param': 'hello'}
        ret = jsonutils.to_primitive(msg)
        self.assertEqual(msg, ret)
