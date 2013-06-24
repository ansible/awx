"""
ns
kombu.serialization
===================

Serialization utilities.

"""
from __future__ import absolute_import

import codecs
import os
import sys

import pickle as pypickle
try:
    import cPickle as cpickle
except ImportError:  # pragma: no cover
    cpickle = None  # noqa

from .exceptions import SerializerNotInstalled, ContentDisallowed
from .utils import entrypoints
from .utils.encoding import str_to_bytes, bytes_t

__all__ = ['pickle', 'encode', 'decode',
           'register', 'unregister']
SKIP_DECODE = frozenset(['binary', 'ascii-8bit'])

if sys.platform.startswith('java'):  # pragma: no cover

    def _decode(t, coding):
        return codecs.getdecoder(coding)(t)[0]
else:
    _decode = codecs.decode

if sys.version_info < (2, 6):  # pragma: no cover
    # cPickle is broken in Python <= 2.5.
    # It unsafely and incorrectly uses relative instead of absolute
    # imports,
    # so e.g.:
    #       exceptions.KeyError
    # becomes:
    #       kombu.exceptions.KeyError
    #
    # Your best choice is to upgrade to Python 2.6,
    # as while the pure pickle version has worse performance,
    # it is the only safe option for older Python versions.
    pickle = pypickle
    pickle_load = pypickle.load
    pickle_loads = pypickle.loads
else:
    pickle = cpickle or pypickle
    pickle_load = pickle.load
    pickle_loads = pickle.loads


# cPickle.loads does not support buffer() objects,
# but we can just create a StringIO and use load.
if sys.version_info[0] == 3:
    from io import BytesIO
else:
    try:
        from cStringIO import StringIO as BytesIO  # noqa
    except ImportError:
        from StringIO import StringIO as BytesIO  # noqa

#: Kombu requires Python 2.5 or later so we use protocol 2 by default.
#: There's a new protocol (3) but this is only supported by Python 3.
pickle_protocol = int(os.environ.get('PICKLE_PROTOCOL', 2))


def pickle_loads(s, load=pickle_load):
    # used to support buffer objects
    return load(BytesIO(s))


def parenthesize_alias(first, second):
    return '%s (%s)' % (first, second) if first else second


class SerializerRegistry(object):
    """The registry keeps track of serialization methods."""

    def __init__(self):
        self._encoders = {}
        self._decoders = {}
        self._default_encode = None
        self._default_content_type = None
        self._default_content_encoding = None
        self._disabled_content_types = set()
        self.type_to_name = {}
        self.name_to_type = {}

    def register(self, name, encoder, decoder, content_type,
                 content_encoding='utf-8'):
        if encoder:
            self._encoders[name] = (content_type, content_encoding, encoder)
        if decoder:
            self._decoders[content_type] = decoder
        self.type_to_name[content_type] = name
        self.name_to_type[name] = content_type

    def enable(self, name):
        if '/' not in name:
            name = self.name_to_type[name]
        self._disabled_content_types.remove(name)

    def disable(self, name):
        if '/' not in name:
            name = self.name_to_type[name]
        self._disabled_content_types.add(name)

    def unregister(self, name):
        try:
            content_type = self.name_to_type[name]
            self._decoders.pop(content_type, None)
            self._encoders.pop(name, None)
            self.type_to_name.pop(content_type, None)
            self.name_to_type.pop(name, None)
        except KeyError:
            raise SerializerNotInstalled(
                'No encoder/decoder installed for %s' % name)

    def _set_default_serializer(self, name):
        """
        Set the default serialization method used by this library.

        :param name: The name of the registered serialization method.
            For example, `json` (default), `pickle`, `yaml`, `msgpack`,
            or any custom methods registered using :meth:`register`.

        :raises SerializerNotInstalled: If the serialization method
            requested is not available.
        """
        try:
            (self._default_content_type, self._default_content_encoding,
             self._default_encode) = self._encoders[name]
        except KeyError:
            raise SerializerNotInstalled(
                'No encoder installed for %s' % name)

    def encode(self, data, serializer=None):
        if serializer == 'raw':
            return raw_encode(data)
        if serializer and not self._encoders.get(serializer):
            raise SerializerNotInstalled(
                'No encoder installed for %s' % serializer)

        # If a raw string was sent, assume binary encoding
        # (it's likely either ASCII or a raw binary file, and a character
        # set of 'binary' will encompass both, even if not ideal.
        if not serializer and isinstance(data, bytes_t):
            # In Python 3+, this would be "bytes"; allow binary data to be
            # sent as a message without getting encoder errors
            return 'application/data', 'binary', data

        # For Unicode objects, force it into a string
        if not serializer and isinstance(data, unicode):
            payload = data.encode('utf-8')
            return 'text/plain', 'utf-8', payload

        if serializer:
            content_type, content_encoding, encoder = \
                self._encoders[serializer]
        else:
            encoder = self._default_encode
            content_type = self._default_content_type
            content_encoding = self._default_content_encoding

        payload = encoder(data)
        return content_type, content_encoding, payload

    def decode(self, data, content_type, content_encoding,
               accept=None, force=False):
        if accept is not None:
            if content_type not in accept:
                raise self._for_untrusted_content(content_type, 'untrusted')
        else:
            if content_type in self._disabled_content_types and not force:
                raise self._for_untrusted_content(content_type, 'disabled')
        content_type = content_type or 'application/data'
        content_encoding = (content_encoding or 'utf-8').lower()

        if data:
            decode = self._decoders.get(content_type)
            if decode:
                return decode(data)
            if content_encoding not in SKIP_DECODE and \
                    not isinstance(data, unicode):
                return _decode(data, content_encoding)
        return data

    def _for_untrusted_content(self, ctype, why):
        return ContentDisallowed(
            'Refusing to decode %(why)s content of type %(type)s' % {
                'why': why,
                'type': parenthesize_alias(self.type_to_name[ctype], ctype),
            },
        )


#: Global registry of serializers/deserializers.
registry = SerializerRegistry()


"""
.. function:: encode(data, serializer=default_serializer)

    Serialize a data structure into a string suitable for sending
    as an AMQP message body.

    :param data: The message data to send. Can be a list,
        dictionary or a string.

    :keyword serializer: An optional string representing
        the serialization method you want the data marshalled
        into. (For example, `json`, `raw`, or `pickle`).

        If :const:`None` (default), then json will be used, unless
        `data` is a :class:`str` or :class:`unicode` object. In this
        latter case, no serialization occurs as it would be
        unnecessary.

        Note that if `serializer` is specified, then that
        serialization method will be used even if a :class:`str`
        or :class:`unicode` object is passed in.

    :returns: A three-item tuple containing the content type
        (e.g., `application/json`), content encoding, (e.g.,
        `utf-8`) and a string containing the serialized
        data.

    :raises SerializerNotInstalled: If the serialization method
            requested is not available.
"""
encode = registry.encode

"""
.. function:: decode(data, content_type, content_encoding):

    Deserialize a data stream as serialized using `encode`
    based on `content_type`.

    :param data: The message data to deserialize.

    :param content_type: The content-type of the data.
        (e.g., `application/json`).

    :param content_encoding: The content-encoding of the data.
        (e.g., `utf-8`, `binary`, or `us-ascii`).

    :returns: The unserialized data.

"""
decode = registry.decode


"""
.. function:: register(name, encoder, decoder, content_type,
                       content_encoding='utf-8'):
    Register a new encoder/decoder.

    :param name: A convenience name for the serialization method.

    :param encoder: A method that will be passed a python data structure
        and should return a string representing the serialized data.
        If :const:`None`, then only a decoder will be registered. Encoding
        will not be possible.

    :param decoder: A method that will be passed a string representing
        serialized data and should return a python data structure.
        If :const:`None`, then only an encoder will be registered.
        Decoding will not be possible.

    :param content_type: The mime-type describing the serialized
        structure.

    :param content_encoding: The content encoding (character set) that
        the `decoder` method will be returning. Will usually be
        utf-8`, `us-ascii`, or `binary`.

"""
register = registry.register


"""
.. function:: unregister(name):
    Unregister registered encoder/decoder.

    :param name: Registered serialization method name.

"""
unregister = registry.unregister


def raw_encode(data):
    """Special case serializer."""
    content_type = 'application/data'
    payload = data
    if isinstance(payload, unicode):
        content_encoding = 'utf-8'
        payload = payload.encode(content_encoding)
    else:
        content_encoding = 'binary'
    return content_type, content_encoding, payload


def register_json():
    """Register a encoder/decoder for JSON serialization."""
    from anyjson import loads, dumps

    def _loads(obj):
        if isinstance(obj, bytes_t):
            obj = obj.decode()
        return loads(obj)

    registry.register('json', dumps, _loads,
                      content_type='application/json',
                      content_encoding='utf-8')


def register_yaml():
    """Register a encoder/decoder for YAML serialization.

    It is slower than JSON, but allows for more data types
    to be serialized. Useful if you need to send data such as dates"""
    try:
        import yaml
        registry.register('yaml', yaml.safe_dump, yaml.safe_load,
                          content_type='application/x-yaml',
                          content_encoding='utf-8')
    except ImportError:

        def not_available(*args, **kwargs):
            """In case a client receives a yaml message, but yaml
            isn't installed."""
            raise SerializerNotInstalled(
                'No decoder installed for YAML. Install the PyYAML library')
        registry.register('yaml', None, not_available, 'application/x-yaml')


if sys.version_info[0] == 3:

    def unpickle(s):
        return pickle_loads(str_to_bytes(s))

else:
    unpickle = pickle_loads  # noqa


def register_pickle():
    """The fastest serialization method, but restricts
    you to python clients."""

    def dumps(obj, dumper=pickle.dumps):
        return dumper(obj, protocol=pickle_protocol)

    registry.register('pickle', dumps, unpickle,
                      content_type='application/x-python-serialize',
                      content_encoding='binary')


def register_msgpack():
    """See http://msgpack.sourceforge.net/"""
    try:
        try:
            from msgpack import packb as dumps, unpackb
            loads = lambda s: unpackb(s, encoding='utf-8')
        except ImportError:
            # msgpack < 0.2.0 and Python 2.5
            from msgpack import packs as dumps, unpacks as loads  # noqa
        registry.register(
            'msgpack', dumps, loads,
            content_type='application/x-msgpack',
            content_encoding='binary')
    except ImportError:

        def not_available(*args, **kwargs):
            """In case a client receives a msgpack message, but yaml
            isn't installed."""
            raise SerializerNotInstalled(
                'No decoder installed for msgpack. '
                'Please install the msgpack library')
        registry.register('msgpack', None, not_available,
                          'application/x-msgpack')

# Register the base serialization methods.
register_json()
register_pickle()
register_yaml()
register_msgpack()

# JSON is assumed to always be available, so is the default.
# (this matches the historical use of kombu.)
registry._set_default_serializer('json')


_setupfuns = {
    'json': register_json,
    'pickle': register_pickle,
    'yaml': register_yaml,
    'msgpack': register_msgpack,
    'application/json': register_json,
    'application/x-yaml': register_yaml,
    'application/x-python-serialize': register_pickle,
    'application/x-msgpack': register_msgpack,
}


def enable_insecure_serializers(choices=['pickle', 'yaml', 'msgpack']):
    """Enable serializers that are considered to be unsafe.

    Will enable ``pickle``, ``yaml`` and ``msgpack`` by default,
    but you can also specify a list of serializers (by name or content type)
    to enable.

    """
    for choice in choices:
        try:
            registry.enable(choice)
        except KeyError:
            pass


def disable_insecure_serializers(allowed=['json']):
    """Disable untrusted serializers.

    Will disable all serializers except ``json``
    or you can specify a list of deserializers to allow.

    .. note::

        Producers will still be able to serialize data
        in these formats, but consumers will not accept
        incoming data using the untrusted content types.

    """
    for name in registry._decoders:
        registry.disable(name)
    if allowed is not None:
        for name in allowed:
            registry.enable(name)

# Load entrypoints from installed extensions
for ep, args in entrypoints('kombu.serializers'):
    register(ep.name, *args)
