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

import functools
import getpass
import hashlib
import inspect
import logging
import sys

from oslo_utils import encodeutils
import prettytable
import six

from keystoneclient import exceptions


logger = logging.getLogger(__name__)


# Decorator for cli-args
def arg(*args, **kwargs):
    def _decorator(func):
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, formatters={}, order_by=None):
    pt = prettytable.PrettyTable([f for f in fields],
                                 caching=False, print_empty=False)
    pt.aligns = ['l' for f in fields]

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                field_name = field.lower().replace(' ', '_')
                data = getattr(o, field_name, '')
                if data is None:
                    data = ''
                row.append(data)
        pt.add_row(row)

    if order_by is None:
        order_by = fields[0]
    encoded = encodeutils.safe_encode(pt.get_string(sortby=order_by))
    if six.PY3:
        encoded = encoded.decode()
    print(encoded)


def _word_wrap(string, max_length=0):
    """wrap long strings to be no longer than max_length."""
    if max_length <= 0:
        return string
    return '\n'.join([string[i:i + max_length] for i in
                     range(0, len(string), max_length)])


def print_dict(d, wrap=0):
    """pretty table prints dictionaries.

    Wrap values to max_length wrap if wrap>0
    """
    pt = prettytable.PrettyTable(['Property', 'Value'],
                                 caching=False, print_empty=False)
    pt.aligns = ['l', 'l']
    for (prop, value) in six.iteritems(d):
        if value is None:
            value = ''
        value = _word_wrap(value, max_length=wrap)
        pt.add_row([prop, value])
    encoded = encodeutils.safe_encode(pt.get_string(sortby='Property'))
    if six.PY3:
        encoded = encoded.decode()
    print(encoded)


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""

    # first try the entity as a string
    try:
        return manager.get(name_or_id)
    except (exceptions.NotFound):
        pass

    # finally try to find entity by name
    try:
        if isinstance(name_or_id, six.binary_type):
            name_or_id = name_or_id.decode('utf-8', 'strict')
        return manager.find(name=name_or_id)
    except exceptions.NotFound:
        msg = ("No %s with a name or ID of '%s' exists." %
               (manager.resource_class.__name__.lower(), name_or_id))
        raise exceptions.CommandError(msg)
    except exceptions.NoUniqueMatch:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exceptions.CommandError(msg)


def unauthenticated(f):
    """Adds 'unauthenticated' attribute to decorated function.

    Usage::

        @unauthenticated
        def mymethod(f):
            ...
    """
    f.unauthenticated = True
    return f


def isunauthenticated(f):
    """Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator.

    Returns True if decorator is set to True, False otherwise.
    """
    return getattr(f, 'unauthenticated', False)


def hash_signed_token(signed_text, mode='md5'):
    hash_ = hashlib.new(mode)
    hash_.update(signed_text)
    return hash_.hexdigest()


def prompt_for_password():
    """Prompt user for password if not provided so the password
    doesn't show up in the bash history.
    """
    if not (hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()):
        # nothing to do
        return

    while True:
        try:
            new_passwd = getpass.getpass('New Password: ')
            rep_passwd = getpass.getpass('Repeat New Password: ')
            if new_passwd == rep_passwd:
                return new_passwd
        except EOFError:
            return


class positional(object):
    """A decorator which enforces only some args may be passed positionally.

    This idea and some of the code was taken from the oauth2 client of the
    google-api client.

    This decorator makes it easy to support Python 3 style key-word only
    parameters. For example, in Python 3 it is possible to write::

      def fn(pos1, *, kwonly1, kwonly2=None):
          ...

    All named parameters after * must be a keyword::

      fn(10, 'kw1', 'kw2')  # Raises exception.
      fn(10, kwonly1='kw1', kwonly2='kw2')  # Ok.

    To replicate this behaviour with the positional decorator you simply
    specify how many arguments may be passed positionally. To replicate the
    example above::

        @positional(1)
        def fn(pos1, kwonly1=None, kwonly2=None):
            ...

    If no default value is provided to a keyword argument, it becomes a
    required keyword argument::

        @positional(0)
        def fn(required_kw):
            ...

    This must be called with the keyword parameter::

        fn()  # Raises exception.
        fn(10)  # Raises exception.
        fn(required_kw=10)  # Ok.

    When defining instance or class methods always remember that in python the
    first positional argument passed is always the instance so you will need to
    account for `self` and `cls`::

        class MyClass(object):

            @positional(2)
            def my_method(self, pos1, kwonly1=None):
                ...

            @classmethod
            @positional(2)
            def my_method(cls, pos1, kwonly1=None):
                ...

    If you would prefer not to account for `self` and `cls` you can use the
    `method` and `classmethod` helpers which do not consider the initial
    positional argument. So the following class is exactly the same as the one
    above::

        class MyClass(object):

            @positional.method(1)
            def my_method(self, pos1, kwonly1=None):
                ...

            @positional.classmethod(1)
            def my_method(cls, pos1, kwonly1=None):
                ...

    If a value isn't provided to the decorator then it will enforce that
    every variable without a default value will be required to be a kwarg::

        @positional()
        def fn(pos1, kwonly1=None):
            ...

        fn(10)  # Ok.
        fn(10, 20)  # Raises exception.
        fn(10, kwonly1=20)  # Ok.

    This behaviour will work with the `positional.method` and
    `positional.classmethod` helper functions as well::

        class MyClass(object):

            @positional.classmethod()
            def my_method(cls, pos1, kwonly1=None):
                ...

        MyClass.my_method(10)  # Ok.
        MyClass.my_method(10, 20)  # Raises exception.
        MyClass.my_method(10, kwonly1=20)  # Ok.

    For compatibility reasons you may wish to not always raise an exception so
    a WARN mode is available. Rather than raise an exception a warning message
    will be logged::

        @positional(1, enforcement=positional.WARN):
        def fn(pos1, kwonly=1):
           ...

    Available modes are:

    - positional.EXCEPT - the default, raise an exception.
    - positional.WARN - log a warning on mistake.
    """

    EXCEPT = 'except'
    WARN = 'warn'

    def __init__(self, max_positional_args=None, enforcement=EXCEPT):
        self._max_positional_args = max_positional_args
        self._enforcement = enforcement

    @classmethod
    def method(cls, max_positional_args=None, enforcement=EXCEPT):
        if max_positional_args is not None:
            max_positional_args += 1

        def f(func):
            return cls(max_positional_args, enforcement)(func)
        return f

    @classmethod
    def classmethod(cls, *args, **kwargs):
        def f(func):
            return classmethod(cls.method(*args, **kwargs)(func))
        return f

    def __call__(self, func):
        if self._max_positional_args is None:
            spec = inspect.getargspec(func)
            self._max_positional_args = len(spec.args) - len(spec.defaults)

        plural = '' if self._max_positional_args == 1 else 's'

        @functools.wraps(func)
        def inner(*args, **kwargs):
            if len(args) > self._max_positional_args:
                message = ('%(name)s takes at most %(max)d positional '
                           'argument%(plural)s (%(given)d given)' %
                           {'name': func.__name__,
                            'max': self._max_positional_args,
                            'given': len(args),
                            'plural': plural})

                if self._enforcement == self.EXCEPT:
                    raise TypeError(message)
                elif self._enforcement == self.WARN:
                    logger.warn(message)

            return func(*args, **kwargs)

        return inner
