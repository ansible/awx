"""
    Based on django-picklefield which is
    Copyright (c) 2009-2010 Gintautas Miliauskas
    but some improvements including not deepcopying values.

    Provides an implementation of a pickled object field.
    Such fields can contain any picklable objects.

    The implementation is taken and adopted from Django snippet #1694
    <http://www.djangosnippets.org/snippets/1694/> by Taavi Taijala,
    which is in turn based on Django snippet #513
    <http://www.djangosnippets.org/snippets/513/> by Oliver Beattie.

"""
from __future__ import absolute_import

from base64 import b64encode, b64decode
from zlib import compress, decompress

from celery.utils.serialization import pickle

from django.db import models

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

DEFAULT_PROTOCOL = 2


class PickledObject(str):
    pass


def maybe_compress(value, do_compress=False):
    if do_compress:
        return compress(value)
    return value


def maybe_decompress(value, do_decompress=False):
    if do_decompress:
        return decompress(value)
    return value


def encode(value, compress_object=False, pickle_protocol=DEFAULT_PROTOCOL):
    return b64encode(maybe_compress(
        pickle.dumps(value, pickle_protocol), compress_object),
    )


def decode(value, compress_object=False):
    return pickle.loads(maybe_decompress(b64decode(value), compress_object))


class PickledObjectField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, compress=False, protocol=DEFAULT_PROTOCOL,
                 *args, **kwargs):
        self.compress = compress
        self.protocol = protocol
        kwargs.setdefault('editable', False)
        super(PickledObjectField, self).__init__(*args, **kwargs)

    def get_default(self):
        if self.has_default():
            return self.default() if callable(self.default) else self.default
        return super(PickledObjectField, self).get_default()

    def to_python(self, value):
        if value is not None:
            try:
                return decode(value, self.compress)
            except Exception:
                if isinstance(value, PickledObject):
                    raise
                return value

    def get_db_prep_value(self, value, **kwargs):
        if value is not None and not isinstance(value, PickledObject):
            return force_text(encode(value, self.compress, self.protocol))
        return value

    def value_to_string(self, obj):
        return self.get_db_prep_value(self._get_val_from_obj(obj))

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value, *args, **kwargs):
        if lookup_type not in ['exact', 'in', 'isnull']:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
        return super(PickledObjectField, self) \
            .get_db_prep_lookup(*args, **kwargs)

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules(
        [], [r'^djcelery\.picklefield\.PickledObjectField'],
    )
