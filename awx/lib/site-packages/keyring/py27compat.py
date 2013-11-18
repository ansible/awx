"""
Compatibility support for Python 2.7. Remove when Python 2.7 support is
no longer required.
"""
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    input = raw_input
except NameError:
    input = input

try:
    unicode_str = unicode
except NameError:
    unicode_str = str

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from itertools import ifilter as filter
except ImportError:
    filter = filter

# Taken from six.py
def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        for slots_var in orig_vars.get('__slots__', ()):
            orig_vars.pop(slots_var)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper
