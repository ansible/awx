# -*- coding: utf-8 -*-

#    Copyright (C) 2012-2013 Yahoo! Inc. All Rights Reserved.
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

import inspect
import types

import six

try:
    _TYPE_TYPE = types.TypeType
except AttributeError:
    _TYPE_TYPE = type

# See: https://docs.python.org/2/library/__builtin__.html#module-__builtin__
# and see https://docs.python.org/2/reference/executionmodel.html (and likely
# others)...
_BUILTIN_MODULES = ('builtins', '__builtin__', '__builtins__', 'exceptions')


def _get_members(obj, exclude_hidden):
    """Yields the members of an object, filtering by hidden/not hidden."""
    for (name, value) in inspect.getmembers(obj):
        if name.startswith("_") and exclude_hidden:
            continue
        yield (name, value)


def get_member_names(obj, exclude_hidden=True):
    """Get all the member names for a object."""
    return [name for (name, _obj) in _get_members(obj, exclude_hidden)]


def get_class_name(obj, fully_qualified=True):
    """Get class name for object.

    If object is a type, fully qualified name of the type is returned.
    Else, fully qualified name of the type of the object is returned.
    For builtin types, just name is returned.
    """
    if not isinstance(obj, six.class_types):
        obj = type(obj)
    try:
        built_in = obj.__module__ in _BUILTIN_MODULES
    except AttributeError:
        pass
    else:
        if built_in:
            try:
                return obj.__qualname__
            except AttributeError:
                return obj.__name__
    pieces = []
    try:
        pieces.append(obj.__qualname__)
    except AttributeError:
        pieces.append(obj.__name__)
    if fully_qualified:
        try:
            pieces.insert(0, obj.__module__)
        except AttributeError:
            pass
    return '.'.join(pieces)


def get_all_class_names(obj, up_to=object):
    """Get class names of object parent classes.

    Iterate over all class names object is instance or subclass of,
    in order of method resolution (mro). If up_to parameter is provided,
    only name of classes that are sublcasses to that class are returned.
    """
    if not isinstance(obj, six.class_types):
        obj = type(obj)
    for cls in obj.mro():
        if issubclass(cls, up_to):
            yield get_class_name(cls)


def get_callable_name(function):
    """Generate a name from callable.

    Tries to do the best to guess fully qualified callable name.
    """
    method_self = get_method_self(function)
    if method_self is not None:
        # This is a bound method.
        if isinstance(method_self, six.class_types):
            # This is a bound class method.
            im_class = method_self
        else:
            im_class = type(method_self)
        try:
            parts = (im_class.__module__, function.__qualname__)
        except AttributeError:
            parts = (im_class.__module__, im_class.__name__, function.__name__)
    elif inspect.ismethod(function) or inspect.isfunction(function):
        # This could be a function, a static method, a unbound method...
        try:
            parts = (function.__module__, function.__qualname__)
        except AttributeError:
            if hasattr(function, 'im_class'):
                # This is a unbound method, which exists only in python 2.x
                im_class = function.im_class
                parts = (im_class.__module__,
                         im_class.__name__, function.__name__)
            else:
                parts = (function.__module__, function.__name__)
    else:
        im_class = type(function)
        if im_class is _TYPE_TYPE:
            im_class = function
        try:
            parts = (im_class.__module__, im_class.__qualname__)
        except AttributeError:
            parts = (im_class.__module__, im_class.__name__)
    return '.'.join(parts)


def get_method_self(method):
    if not inspect.ismethod(method):
        return None
    try:
        return six.get_method_self(method)
    except AttributeError:
        return None


def is_same_callback(callback1, callback2, strict=True):
    """Returns if the two callbacks are the same."""
    if callback1 is callback2:
        # This happens when plain methods are given (or static/non-bound
        # methods).
        return True
    if callback1 == callback2:
        if not strict:
            return True
        # Two bound methods are equal if functions themselves are equal and
        # objects they are applied to are equal. This means that a bound
        # method could be the same bound method on another object if the
        # objects have __eq__ methods that return true (when in fact it is a
        # different bound method). Python u so crazy!
        try:
            self1 = six.get_method_self(callback1)
            self2 = six.get_method_self(callback2)
            return self1 is self2
        except AttributeError:
            pass
    return False


def is_bound_method(method):
    """Returns if the given method is bound to an object."""
    return bool(get_method_self(method))


def is_subclass(obj, cls):
    """Returns if the object is class and it is subclass of a given class."""
    return inspect.isclass(obj) and issubclass(obj, cls)


def _get_arg_spec(function):
    if isinstance(function, _TYPE_TYPE):
        bound = True
        function = function.__init__
    elif isinstance(function, (types.FunctionType, types.MethodType)):
        bound = is_bound_method(function)
        function = getattr(function, '__wrapped__', function)
    else:
        function = function.__call__
        bound = is_bound_method(function)
    return inspect.getargspec(function), bound


def get_callable_args(function, required_only=False):
    """Get names of callable arguments.

    Special arguments (like *args and **kwargs) are not included into
    output.

    If required_only is True, optional arguments (with default values)
    are not included into output.
    """
    argspec, bound = _get_arg_spec(function)
    f_args = argspec.args
    if required_only and argspec.defaults:
        f_args = f_args[:-len(argspec.defaults)]
    if bound:
        f_args = f_args[1:]
    return f_args


def accepts_kwargs(function):
    """Returns True if function accepts kwargs."""
    argspec, _bound = _get_arg_spec(function)
    return bool(argspec.keywords)
