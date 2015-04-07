# -*- coding: utf-8 -*-

#    Copyright (C) 2012 Yahoo! Inc. All Rights Reserved.
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

from oslotest import base as test_base
import six
import testtools

from oslo_utils import reflection


if six.PY3:
    RUNTIME_ERROR_CLASSES = ['RuntimeError', 'Exception',
                             'BaseException', 'object']
else:
    RUNTIME_ERROR_CLASSES = ['RuntimeError', 'StandardError', 'Exception',
                             'BaseException', 'object']


def dummy_decorator(f):

    @six.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def mere_function(a, b):
    pass


def function_with_defs(a, b, optional=None):
    pass


def function_with_kwargs(a, b, **kwargs):
    pass


class Class(object):

    def method(self, c, d):
        pass

    @staticmethod
    def static_method(e, f):
        pass

    @classmethod
    def class_method(cls, g, h):
        pass


class CallableClass(object):
    def __call__(self, i, j):
        pass


class ClassWithInit(object):
    def __init__(self, k, l):
        pass


class CallbackEqualityTest(test_base.BaseTestCase):
    def test_different_simple_callbacks(self):

        def a():
            pass

        def b():
            pass

        self.assertFalse(reflection.is_same_callback(a, b))

    def test_static_instance_callbacks(self):

        class A(object):

            @staticmethod
            def b(a, b, c):
                pass

        a = A()
        b = A()

        self.assertTrue(reflection.is_same_callback(a.b, b.b))

    def test_different_instance_callbacks(self):

        class A(object):
            def b(self):
                pass

            def __eq__(self, other):
                return True

        b = A()
        c = A()

        self.assertFalse(reflection.is_same_callback(b.b, c.b))
        self.assertTrue(reflection.is_same_callback(b.b, c.b, strict=False))


class GetCallableNameTest(test_base.BaseTestCase):

    def test_mere_function(self):
        name = reflection.get_callable_name(mere_function)
        self.assertEqual('.'.join((__name__, 'mere_function')), name)

    def test_method(self):
        name = reflection.get_callable_name(Class.method)
        self.assertEqual('.'.join((__name__, 'Class', 'method')), name)

    def test_instance_method(self):
        name = reflection.get_callable_name(Class().method)
        self.assertEqual('.'.join((__name__, 'Class', 'method')), name)

    def test_static_method(self):
        name = reflection.get_callable_name(Class.static_method)
        if six.PY3:
            self.assertEqual('.'.join((__name__, 'Class', 'static_method')),
                             name)
        else:
            # NOTE(imelnikov): static method are just functions, class name
            # is not recorded anywhere in them.
            self.assertEqual('.'.join((__name__, 'static_method')), name)

    def test_class_method(self):
        name = reflection.get_callable_name(Class.class_method)
        self.assertEqual('.'.join((__name__, 'Class', 'class_method')), name)

    def test_constructor(self):
        name = reflection.get_callable_name(Class)
        self.assertEqual('.'.join((__name__, 'Class')), name)

    def test_callable_class(self):
        name = reflection.get_callable_name(CallableClass())
        self.assertEqual('.'.join((__name__, 'CallableClass')), name)

    def test_callable_class_call(self):
        name = reflection.get_callable_name(CallableClass().__call__)
        self.assertEqual('.'.join((__name__, 'CallableClass',
                                   '__call__')), name)


# These extended/special case tests only work on python 3, due to python 2
# being broken/incorrect with regard to these special cases...
@testtools.skipIf(not six.PY3, 'python 3.x is not currently available')
class GetCallableNameTestExtended(test_base.BaseTestCase):
    # Tests items in http://legacy.python.org/dev/peps/pep-3155/

    class InnerCallableClass(object):
        def __call__(self):
            pass

    def test_inner_callable_class(self):
        obj = self.InnerCallableClass()
        name = reflection.get_callable_name(obj.__call__)
        expected_name = '.'.join((__name__, 'GetCallableNameTestExtended',
                                  'InnerCallableClass', '__call__'))
        self.assertEqual(expected_name, name)

    def test_inner_callable_function(self):
        def a():

            def b():
                pass

            return b

        name = reflection.get_callable_name(a())
        expected_name = '.'.join((__name__, 'GetCallableNameTestExtended',
                                  'test_inner_callable_function', '<locals>',
                                  'a', '<locals>', 'b'))
        self.assertEqual(expected_name, name)

    def test_inner_class(self):
        obj = self.InnerCallableClass()
        name = reflection.get_callable_name(obj)
        expected_name = '.'.join((__name__,
                                  'GetCallableNameTestExtended',
                                  'InnerCallableClass'))
        self.assertEqual(expected_name, name)


class GetCallableArgsTest(test_base.BaseTestCase):

    def test_mere_function(self):
        result = reflection.get_callable_args(mere_function)
        self.assertEqual(['a', 'b'], result)

    def test_function_with_defaults(self):
        result = reflection.get_callable_args(function_with_defs)
        self.assertEqual(['a', 'b', 'optional'], result)

    def test_required_only(self):
        result = reflection.get_callable_args(function_with_defs,
                                              required_only=True)
        self.assertEqual(['a', 'b'], result)

    def test_method(self):
        result = reflection.get_callable_args(Class.method)
        self.assertEqual(['self', 'c', 'd'], result)

    def test_instance_method(self):
        result = reflection.get_callable_args(Class().method)
        self.assertEqual(['c', 'd'], result)

    def test_class_method(self):
        result = reflection.get_callable_args(Class.class_method)
        self.assertEqual(['g', 'h'], result)

    def test_class_constructor(self):
        result = reflection.get_callable_args(ClassWithInit)
        self.assertEqual(['k', 'l'], result)

    def test_class_with_call(self):
        result = reflection.get_callable_args(CallableClass())
        self.assertEqual(['i', 'j'], result)

    def test_decorators_work(self):
        @dummy_decorator
        def special_fun(x, y):
            pass
        result = reflection.get_callable_args(special_fun)
        self.assertEqual(['x', 'y'], result)


class AcceptsKwargsTest(test_base.BaseTestCase):

    def test_no_kwargs(self):
        self.assertEqual(False, reflection.accepts_kwargs(mere_function))

    def test_with_kwargs(self):
        self.assertEqual(True, reflection.accepts_kwargs(function_with_kwargs))


class GetClassNameTest(test_base.BaseTestCase):

    def test_std_exception(self):
        name = reflection.get_class_name(RuntimeError)
        self.assertEqual('RuntimeError', name)

    def test_class(self):
        name = reflection.get_class_name(Class)
        self.assertEqual('.'.join((__name__, 'Class')), name)

    def test_instance(self):
        name = reflection.get_class_name(Class())
        self.assertEqual('.'.join((__name__, 'Class')), name)

    def test_int(self):
        name = reflection.get_class_name(42)
        self.assertEqual('int', name)


class GetAllClassNamesTest(test_base.BaseTestCase):

    def test_std_class(self):
        names = list(reflection.get_all_class_names(RuntimeError))
        self.assertEqual(RUNTIME_ERROR_CLASSES, names)

    def test_std_class_up_to(self):
        names = list(reflection.get_all_class_names(RuntimeError,
                                                    up_to=Exception))
        self.assertEqual(RUNTIME_ERROR_CLASSES[:-2], names)
