import datetime
import decimal
import itertools
import re
import time
import urllib2
import uuid
import warnings
from operator import itemgetter

try:
    import dateutil
except ImportError:
    dateutil = None
else:
    import dateutil.parser

import pymongo
import gridfs
from bson import Binary, DBRef, SON, ObjectId

from mongoengine.errors import ValidationError
from mongoengine.python_support import (PY3, bin_type, txt_type,
                                        str_types, StringIO)
from base import (BaseField, ComplexBaseField, ObjectIdField, GeoJsonBaseField,
                  get_document, BaseDocument)
from queryset import DO_NOTHING, QuerySet
from document import Document, EmbeddedDocument
from connection import get_db, DEFAULT_CONNECTION_NAME

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

__all__ = [
    'StringField', 'URLField', 'EmailField', 'IntField', 'LongField',
    'FloatField', 'DecimalField', 'BooleanField', 'DateTimeField',
    'ComplexDateTimeField', 'EmbeddedDocumentField', 'ObjectIdField',
    'GenericEmbeddedDocumentField', 'DynamicField', 'ListField',
    'SortedListField', 'EmbeddedDocumentListField', 'DictField',
    'MapField', 'ReferenceField', 'CachedReferenceField',
    'GenericReferenceField', 'BinaryField', 'GridFSError', 'GridFSProxy',
    'FileField', 'ImageGridFsProxy', 'ImproperlyConfigured', 'ImageField',
    'GeoPointField', 'PointField', 'LineStringField', 'PolygonField',
    'SequenceField', 'UUIDField', 'MultiPointField', 'MultiLineStringField',
    'MultiPolygonField', 'GeoJsonBaseField']


RECURSIVE_REFERENCE_CONSTANT = 'self'


class StringField(BaseField):

    """A unicode string field.
    """

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super(StringField, self).__init__(**kwargs)

    def to_python(self, value):
        if isinstance(value, unicode):
            return value
        try:
            value = value.decode('utf-8')
        except:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, basestring):
            self.error('StringField only accepts string values')

        if self.max_length is not None and len(value) > self.max_length:
            self.error('String value is too long')

        if self.min_length is not None and len(value) < self.min_length:
            self.error('String value is too short')

        if self.regex is not None and self.regex.match(value) is None:
            self.error('String value did not match validation regex')

    def lookup_member(self, member_name):
        return None

    def prepare_query_value(self, op, value):
        if not isinstance(op, basestring):
            return value

        if op.lstrip('i') in ('startswith', 'endswith', 'contains', 'exact'):
            flags = 0
            if op.startswith('i'):
                flags = re.IGNORECASE
                op = op.lstrip('i')

            regex = r'%s'
            if op == 'startswith':
                regex = r'^%s'
            elif op == 'endswith':
                regex = r'%s$'
            elif op == 'exact':
                regex = r'^%s$'

            # escape unsafe characters which could lead to a re.error
            value = re.escape(value)
            value = re.compile(regex % value, flags)
        return value


class URLField(StringField):

    """A field that validates input as an URL.

    .. versionadded:: 0.3
    """

    _URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __init__(self, verify_exists=False, url_regex=None, **kwargs):
        self.verify_exists = verify_exists
        self.url_regex = url_regex or self._URL_REGEX
        super(URLField, self).__init__(**kwargs)

    def validate(self, value):
        if not self.url_regex.match(value):
            self.error('Invalid URL: %s' % value)
            return

        if self.verify_exists:
            warnings.warn(
                "The URLField verify_exists argument has intractable security "
                "and performance issues. Accordingly, it has been deprecated.",
                DeprecationWarning)
            try:
                request = urllib2.Request(value)
                urllib2.urlopen(request)
            except Exception, e:
                self.error('This URL appears to be a broken link: %s' % e)


class EmailField(StringField):

    """A field that validates input as an E-Mail-Address.

    .. versionadded:: 0.4
    """

    EMAIL_REGEX = re.compile(
        # dot-atom
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'
        # domain (max length of an ICAAN TLD is 22 characters)
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,253}[A-Z0-9])?\.)+[A-Z]{2,22}$', re.IGNORECASE
    )

    def validate(self, value):
        if not EmailField.EMAIL_REGEX.match(value):
            self.error('Invalid Mail-address: %s' % value)
        super(EmailField, self).validate(value)


class IntField(BaseField):

    """An 32-bit integer field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(IntField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        try:
            value = int(value)
        except:
            self.error('%s could not be converted to int' % value)

        if self.min_value is not None and value < self.min_value:
            self.error('Integer value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Integer value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return int(value)


class LongField(BaseField):

    """An 64-bit integer field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(LongField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = long(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        try:
            value = long(value)
        except:
            self.error('%s could not be converted to long' % value)

        if self.min_value is not None and value < self.min_value:
            self.error('Long value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Long value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return long(value)


class FloatField(BaseField):

    """An floating point number field.
    """

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(FloatField, self).__init__(**kwargs)

    def to_python(self, value):
        try:
            value = float(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            self.error('FloatField only accepts float values')

        if self.min_value is not None and value < self.min_value:
            self.error('Float value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Float value is too large')

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return float(value)


class DecimalField(BaseField):

    """A fixed-point decimal number field.

    .. versionchanged:: 0.8
    .. versionadded:: 0.3
    """

    def __init__(self, min_value=None, max_value=None, force_string=False,
                 precision=2, rounding=decimal.ROUND_HALF_UP, **kwargs):
        """
        :param min_value: Validation rule for the minimum acceptable value.
        :param max_value: Validation rule for the maximum acceptable value.
        :param force_string: Store as a string.
        :param precision: Number of decimal places to store.
        :param rounding: The rounding rule from the python decimal library:

            - decimal.ROUND_CEILING (towards Infinity)
            - decimal.ROUND_DOWN (towards zero)
            - decimal.ROUND_FLOOR (towards -Infinity)
            - decimal.ROUND_HALF_DOWN (to nearest with ties going towards zero)
            - decimal.ROUND_HALF_EVEN (to nearest with ties going to nearest even integer)
            - decimal.ROUND_HALF_UP (to nearest with ties going away from zero)
            - decimal.ROUND_UP (away from zero)
            - decimal.ROUND_05UP (away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise towards zero)

            Defaults to: ``decimal.ROUND_HALF_UP``

        """
        self.min_value = min_value
        self.max_value = max_value
        self.force_string = force_string
        self.precision = precision
        self.rounding = rounding

        super(DecimalField, self).__init__(**kwargs)

    def to_python(self, value):
        if value is None:
            return value

        # Convert to string for python 2.6 before casting to Decimal
        try:
            value = decimal.Decimal("%s" % value)
        except decimal.InvalidOperation:
            return value
        return value.quantize(decimal.Decimal(".%s" % ("0" * self.precision)), rounding=self.rounding)

    def to_mongo(self, value, use_db_field=True):
        if value is None:
            return value
        if self.force_string:
            return unicode(value)
        return float(self.to_python(value))

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, basestring):
                value = unicode(value)
            try:
                value = decimal.Decimal(value)
            except Exception, exc:
                self.error('Could not convert value to decimal: %s' % exc)

        if self.min_value is not None and value < self.min_value:
            self.error('Decimal value is too small')

        if self.max_value is not None and value > self.max_value:
            self.error('Decimal value is too large')

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)


class BooleanField(BaseField):

    """A boolean field type.

    .. versionadded:: 0.1.2
    """

    def to_python(self, value):
        try:
            value = bool(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, bool):
            self.error('BooleanField only accepts boolean values')


class DateTimeField(BaseField):

    """A datetime field.

    Uses the python-dateutil library if available alternatively use time.strptime
    to parse the dates.  Note: python-dateutil's parser is fully featured and when
    installed you can utilise it to convert varying types of date formats into valid
    python datetime objects.

    Note: Microseconds are rounded to the nearest millisecond.
      Pre UTC microsecond support is effectively broken.
      Use :class:`~mongoengine.fields.ComplexDateTimeField` if you
      need accurate microsecond support.
    """

    def validate(self, value):
        new_value = self.to_mongo(value)
        if not isinstance(new_value, (datetime.datetime, datetime.date)):
            self.error(u'cannot parse date "%s"' % value)

    def to_mongo(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if callable(value):
            return value()

        if not isinstance(value, basestring):
            return None

        # Attempt to parse a datetime:
        if dateutil:
            try:
                return dateutil.parser.parse(value)
            except (TypeError, ValueError):
                return None

        # split usecs, because they are not recognized by strptime.
        if '.' in value:
            try:
                value, usecs = value.split('.')
                usecs = int(usecs)
            except ValueError:
                return None
        else:
            usecs = 0
        kwargs = {'microsecond': usecs}
        try:  # Seconds are optional, so try converting seconds first.
            return datetime.datetime(*time.strptime(value,
                                                    '%Y-%m-%d %H:%M:%S')[:6], **kwargs)
        except ValueError:
            try:  # Try without seconds.
                return datetime.datetime(*time.strptime(value,
                                                        '%Y-%m-%d %H:%M')[:5], **kwargs)
            except ValueError:  # Try without hour/minutes/seconds.
                try:
                    return datetime.datetime(*time.strptime(value,
                                                            '%Y-%m-%d')[:3], **kwargs)
                except ValueError:
                    return None

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)


class ComplexDateTimeField(StringField):

    """
    ComplexDateTimeField handles microseconds exactly instead of rounding
    like DateTimeField does.

    Derives from a StringField so you can do `gte` and `lte` filtering by
    using lexicographical comparison when filtering / sorting strings.

    The stored string has the following format:

        YYYY,MM,DD,HH,MM,SS,NNNNNN

    Where NNNNNN is the number of microseconds of the represented `datetime`.
    The `,` as the separator can be easily modified by passing the `separator`
    keyword when initializing the field.

    .. versionadded:: 0.5
    """

    def __init__(self, separator=',', **kwargs):
        self.names = ['year', 'month', 'day', 'hour', 'minute', 'second',
                      'microsecond']
        self.separtor = separator
        super(ComplexDateTimeField, self).__init__(**kwargs)

    def _leading_zero(self, number):
        """
        Converts the given number to a string.

        If it has only one digit, a leading zero so as it has always at least
        two digits.
        """
        if int(number) < 10:
            return "0%s" % number
        else:
            return str(number)

    def _convert_from_datetime(self, val):
        """
        Convert a `datetime` object to a string representation (which will be
        stored in MongoDB). This is the reverse function of
        `_convert_from_string`.

        >>> a = datetime(2011, 6, 8, 20, 26, 24, 192284)
        >>> RealDateTimeField()._convert_from_datetime(a)
        '2011,06,08,20,26,24,192284'
        """
        data = []
        for name in self.names:
            data.append(self._leading_zero(getattr(val, name)))
        return ','.join(data)

    def _convert_from_string(self, data):
        """
        Convert a string representation to a `datetime` object (the object you
        will manipulate). This is the reverse function of
        `_convert_from_datetime`.

        >>> a = '2011,06,08,20,26,24,192284'
        >>> ComplexDateTimeField()._convert_from_string(a)
        datetime.datetime(2011, 6, 8, 20, 26, 24, 192284)
        """
        data = data.split(',')
        data = map(int, data)
        values = {}
        for i in range(7):
            values[self.names[i]] = data[i]
        return datetime.datetime(**values)

    def __get__(self, instance, owner):
        data = super(ComplexDateTimeField, self).__get__(instance, owner)
        if data is None:
            return None if self.null else datetime.datetime.now()
        if isinstance(data, datetime.datetime):
            return data
        return self._convert_from_string(data)

    def __set__(self, instance, value):
        value = self._convert_from_datetime(value) if value else value
        return super(ComplexDateTimeField, self).__set__(instance, value)

    def validate(self, value):
        value = self.to_python(value)
        if not isinstance(value, datetime.datetime):
            self.error('Only datetime objects may used in a '
                       'ComplexDateTimeField')

    def to_python(self, value):
        original_value = value
        try:
            return self._convert_from_string(value)
        except:
            return original_value

    def to_mongo(self, value):
        value = self.to_python(value)
        return self._convert_from_datetime(value)

    def prepare_query_value(self, op, value):
        return self._convert_from_datetime(value)


class EmbeddedDocumentField(BaseField):

    """An embedded document field - with a declared document_type.
    Only valid values are subclasses of :class:`~mongoengine.EmbeddedDocument`.
    """

    def __init__(self, document_type, **kwargs):
        if not isinstance(document_type, basestring):
            if not issubclass(document_type, EmbeddedDocument):
                self.error('Invalid embedded document class provided to an '
                           'EmbeddedDocumentField')
        self.document_type_obj = document_type
        super(EmbeddedDocumentField, self).__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def to_python(self, value):
        if not isinstance(value, self.document_type):
            return self.document_type._from_son(value)
        return value

    def to_mongo(self, value, use_db_field=True, fields=[]):
        if not isinstance(value, self.document_type):
            return value
        return self.document_type.to_mongo(value, use_db_field,
                                           fields=fields)

    def validate(self, value, clean=True):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            self.error('Invalid embedded document instance provided to an '
                       'EmbeddedDocumentField')
        self.document_type.validate(value, clean)

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)


class GenericEmbeddedDocumentField(BaseField):

    """A generic embedded document field - allows any
    :class:`~mongoengine.EmbeddedDocument` to be stored.

    Only valid values are subclasses of :class:`~mongoengine.EmbeddedDocument`.

    .. note ::
        You can use the choices param to limit the acceptable
        EmbeddedDocument types
    """

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)

    def to_python(self, value):
        if isinstance(value, dict):
            doc_cls = get_document(value['_cls'])
            value = doc_cls._from_son(value)

        return value

    def validate(self, value, clean=True):
        if not isinstance(value, EmbeddedDocument):
            self.error('Invalid embedded document instance provided to an '
                       'GenericEmbeddedDocumentField')

        value.validate(clean=clean)

    def to_mongo(self, document, use_db_field=True):
        if document is None:
            return None

        data = document.to_mongo(use_db_field)
        if not '_cls' in data:
            data['_cls'] = document._class_name
        return data


class DynamicField(BaseField):

    """A truly dynamic field type capable of handling different and varying
    types of data.

    Used by :class:`~mongoengine.DynamicDocument` to handle dynamic data"""

    def to_mongo(self, value):
        """Convert a Python type to a MongoDB compatible type.
        """

        if isinstance(value, basestring):
            return value

        if hasattr(value, 'to_mongo'):
            cls = value.__class__
            val = value.to_mongo()
            # If we its a document thats not inherited add _cls
            if (isinstance(value,   Document)):
                val = {"_ref": value.to_dbref(), "_cls": cls.__name__}
            if (isinstance(value, EmbeddedDocument)):
                val['_cls'] = cls.__name__
            return val

        if not isinstance(value, (dict, list, tuple)):
            return value

        is_list = False
        if not hasattr(value, 'items'):
            is_list = True
            value = dict([(k, v) for k, v in enumerate(value)])

        data = {}
        for k, v in value.iteritems():
            data[k] = self.to_mongo(v)

        value = data
        if is_list:  # Convert back to a list
            value = [v for k, v in sorted(data.iteritems(), key=itemgetter(0))]
        return value

    def to_python(self, value):
        if isinstance(value, dict) and '_cls' in value:
            doc_cls = get_document(value['_cls'])
            if '_ref' in value:
                value = doc_cls._get_db().dereference(value['_ref'])
            return doc_cls._from_son(value)

        return super(DynamicField, self).to_python(value)

    def lookup_member(self, member_name):
        return member_name

    def prepare_query_value(self, op, value):
        if isinstance(value, basestring):
            from mongoengine.fields import StringField
            return StringField().prepare_query_value(op, value)
        return self.to_mongo(value)

    def validate(self, value, clean=True):
        if hasattr(value, "validate"):
            value.validate(clean=clean)


class ListField(ComplexBaseField):

    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the database.

    If using with ReferenceFields see: :ref:`one-to-many-with-listfields`

    .. note::
        Required means it cannot be empty - as the default for ListFields is []
    """

    def __init__(self, field=None, **kwargs):
        self.field = field
        kwargs.setdefault('default', lambda: [])
        super(ListField, self).__init__(**kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if (not isinstance(value, (list, tuple, QuerySet)) or
                isinstance(value, basestring)):
            self.error('Only lists and tuples may be used in a list field')
        super(ListField, self).validate(value)

    def prepare_query_value(self, op, value):
        if self.field:
            if op in ('set', 'unset') and (not isinstance(value, basestring)
                                           and not isinstance(value, BaseDocument)
                                           and hasattr(value, '__iter__')):
                return [self.field.prepare_query_value(op, v) for v in value]
            return self.field.prepare_query_value(op, value)
        return super(ListField, self).prepare_query_value(op, value)


class EmbeddedDocumentListField(ListField):
    """A :class:`~mongoengine.ListField` designed specially to hold a list of
    embedded documents to provide additional query helpers.

    .. note::
        The only valid list values are subclasses of
        :class:`~mongoengine.EmbeddedDocument`.

    .. versionadded:: 0.9

    """

    def __init__(self, document_type, *args, **kwargs):
        """
        :param document_type: The type of
         :class:`~mongoengine.EmbeddedDocument` the list will hold.
        :param args: Arguments passed directly into the parent
         :class:`~mongoengine.ListField`.
        :param kwargs: Keyword arguments passed directly into the parent
         :class:`~mongoengine.ListField`.
        """
        super(EmbeddedDocumentListField, self).__init__(
            field=EmbeddedDocumentField(document_type), **kwargs
        )


class SortedListField(ListField):

    """A ListField that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.

    .. warning::
        There is a potential race condition when handling lists.  If you set /
        save the whole list then other processes trying to save the whole list
        as well could overwrite changes.  The safest way to append to a list is
        to perform a push operation.

    .. versionadded:: 0.4
    .. versionchanged:: 0.6 - added reverse keyword
    """

    _ordering = None
    _order_reverse = False

    def __init__(self, field, **kwargs):
        if 'ordering' in kwargs.keys():
            self._ordering = kwargs.pop('ordering')
        if 'reverse' in kwargs.keys():
            self._order_reverse = kwargs.pop('reverse')
        super(SortedListField, self).__init__(field, **kwargs)

    def to_mongo(self, value):
        value = super(SortedListField, self).to_mongo(value)
        if self._ordering is not None:
            return sorted(value, key=itemgetter(self._ordering),
                          reverse=self._order_reverse)
        return sorted(value, reverse=self._order_reverse)


def key_not_string(d):
    """ Helper function to recursively determine if any key in a dictionary is
    not a string.
    """
    for k, v in d.items():
        if not isinstance(k, basestring) or (isinstance(v, dict) and key_not_string(v)):
            return True


def key_has_dot_or_dollar(d):
    """ Helper function to recursively determine if any key in a dictionary
    contains a dot or a dollar sign.
    """
    for k, v in d.items():
        if ('.' in k or '$' in k) or (isinstance(v, dict) and key_has_dot_or_dollar(v)):
            return True


class DictField(ComplexBaseField):

    """A dictionary field that wraps a standard Python dictionary. This is
    similar to an embedded document, but the structure is not defined.

    .. note::
        Required means it cannot be empty - as the default for DictFields is {}

    .. versionadded:: 0.3
    .. versionchanged:: 0.5 - Can now handle complex / varying types of data
    """

    def __init__(self, basecls=None, field=None, *args, **kwargs):
        self.field = field
        self.basecls = basecls or BaseField
        if not issubclass(self.basecls, BaseField):
            self.error('DictField only accepts dict values')
        kwargs.setdefault('default', lambda: {})
        super(DictField, self).__init__(*args, **kwargs)

    def validate(self, value):
        """Make sure that a list of valid fields is being used.
        """
        if not isinstance(value, dict):
            self.error('Only dictionaries may be used in a DictField')

        if key_not_string(value):
            msg = ("Invalid dictionary key - documents must "
                   "have only string keys")
            self.error(msg)
        if key_has_dot_or_dollar(value):
            self.error('Invalid dictionary key name - keys may not contain "."'
                       ' or "$" characters')
        super(DictField, self).validate(value)

    def lookup_member(self, member_name):
        return DictField(basecls=self.basecls, db_field=member_name)

    def prepare_query_value(self, op, value):
        match_operators = ['contains', 'icontains', 'startswith',
                           'istartswith', 'endswith', 'iendswith',
                           'exact', 'iexact']

        if op in match_operators and isinstance(value, basestring):
            return StringField().prepare_query_value(op, value)

        if hasattr(self.field, 'field'):
            if op in ('set', 'unset') and isinstance(value, dict):
                return dict(
                    (k, self.field.prepare_query_value(op, v))
                    for k, v in value.items())
            return self.field.prepare_query_value(op, value)

        return super(DictField, self).prepare_query_value(op, value)


class MapField(DictField):

    """A field that maps a name to a specified field type. Similar to
    a DictField, except the 'value' of each item must match the specified
    field type.

    .. versionadded:: 0.5
    """

    def __init__(self, field=None, *args, **kwargs):
        if not isinstance(field, BaseField):
            self.error('Argument to MapField constructor must be a valid '
                       'field')
        super(MapField, self).__init__(field=field, *args, **kwargs)


class ReferenceField(BaseField):

    """A reference to a document that will be automatically dereferenced on
    access (lazily).

    Use the `reverse_delete_rule` to handle what should happen if the document
    the field is referencing is deleted.  EmbeddedDocuments, DictFields and
    MapFields does not support reverse_delete_rule and an `InvalidDocumentError`
    will be raised if trying to set on one of these Document / Field types.

    The options are:

      * DO_NOTHING  - don't do anything (default).
      * NULLIFY     - Updates the reference to null.
      * CASCADE     - Deletes the documents associated with the reference.
      * DENY        - Prevent the deletion of the reference object.
      * PULL        - Pull the reference from a :class:`~mongoengine.fields.ListField`
                      of references

    Alternative syntax for registering delete rules (useful when implementing
    bi-directional delete rules)

    .. code-block:: python

        class Bar(Document):
            content = StringField()
            foo = ReferenceField('Foo')

        Bar.register_delete_rule(Foo, 'bar', NULLIFY)

    .. note ::
        `reverse_delete_rule` does not trigger pre / post delete signals to be
        triggered.

    .. versionchanged:: 0.5 added `reverse_delete_rule`
    """

    def __init__(self, document_type, dbref=False,
                 reverse_delete_rule=DO_NOTHING, **kwargs):
        """Initialises the Reference Field.

        :param dbref:  Store the reference as :class:`~pymongo.dbref.DBRef`
          or as the :class:`~pymongo.objectid.ObjectId`.id .
        :param reverse_delete_rule: Determines what to do when the referring
          object is deleted
        """
        if not isinstance(document_type, basestring):
            if not issubclass(document_type, (Document, basestring)):
                self.error('Argument to ReferenceField constructor must be a '
                           'document class or a string')

        self.dbref = dbref
        self.document_type_obj = document_type
        self.reverse_delete_rule = reverse_delete_rule
        super(ReferenceField, self).__init__(**kwargs)

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def __get__(self, instance, owner):
        """Descriptor to allow lazy dereferencing.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        value = instance._data.get(self.name)
        self._auto_dereference = instance._fields[self.name]._auto_dereference
        # Dereference DBRefs
        if self._auto_dereference and isinstance(value, DBRef):
            value = self.document_type._get_db().dereference(value)
            if value is not None:
                instance._data[self.name] = self.document_type._from_son(value)

        return super(ReferenceField, self).__get__(instance, owner)

    def to_mongo(self, document):
        if isinstance(document, DBRef):
            if not self.dbref:
                return document.id
            return document

        id_field_name = self.document_type._meta['id_field']
        id_field = self.document_type._fields[id_field_name]

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.pk
            if id_ is None:
                self.error('You can only reference documents once they have'
                           ' been saved to the database')
        else:
            id_ = document

        id_ = id_field.to_mongo(id_)
        if self.dbref:
            collection = self.document_type._get_collection_name()
            return DBRef(collection, id_)

        return id_

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type.
        """
        if (not self.dbref and
                not isinstance(value, (DBRef, Document, EmbeddedDocument))):
            collection = self.document_type._get_collection_name()
            value = DBRef(collection, self.document_type.id.to_python(value))
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        return self.to_mongo(value)

    def validate(self, value):

        if not isinstance(value, (self.document_type, DBRef)):
            self.error("A ReferenceField only accepts DBRef or documents")

        if isinstance(value, Document) and value.id is None:
            self.error('You can only reference documents once they have been '
                       'saved to the database')

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)


class CachedReferenceField(BaseField):

    """
    A referencefield with cache fields to porpuse pseudo-joins
    .. versionadded:: 0.9
    """

    def __init__(self, document_type, fields=[], auto_sync=True, **kwargs):
        """Initialises the Cached Reference Field.

        :param fields:  A list of fields to be cached in document
        :param auto_sync: if True documents are auto updated.
        """
        if not isinstance(document_type, basestring) and \
                not issubclass(document_type, (Document, basestring)):

            self.error('Argument to CachedReferenceField constructor must be a'
                       ' document class or a string')

        self.auto_sync = auto_sync
        self.document_type_obj = document_type
        self.fields = fields
        super(CachedReferenceField, self).__init__(**kwargs)

    def start_listener(self):
        from mongoengine import signals
        signals.post_save.connect(self.on_document_pre_save,
                                  sender=self.document_type)

    def on_document_pre_save(self, sender, document, created, **kwargs):
        if not created:
            update_kwargs = dict(
                ('set__%s__%s' % (self.name, k), v)
                for k, v in document._delta()[0].items()
                if k in self.fields)

            if update_kwargs:
                filter_kwargs = {}
                filter_kwargs[self.name] = document

                self.owner_document.objects(
                    **filter_kwargs).update(**update_kwargs)

    def to_python(self, value):
        if isinstance(value, dict):
            collection = self.document_type._get_collection_name()
            value = DBRef(
                collection, self.document_type.id.to_python(value['_id']))

        return value

    @property
    def document_type(self):
        if isinstance(self.document_type_obj, basestring):
            if self.document_type_obj == RECURSIVE_REFERENCE_CONSTANT:
                self.document_type_obj = self.owner_document
            else:
                self.document_type_obj = get_document(self.document_type_obj)
        return self.document_type_obj

    def __get__(self, instance, owner):
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        value = instance._data.get(self.name)
        self._auto_dereference = instance._fields[self.name]._auto_dereference
        # Dereference DBRefs
        if self._auto_dereference and isinstance(value, DBRef):
            value = self.document_type._get_db().dereference(value)
            if value is not None:
                instance._data[self.name] = self.document_type._from_son(value)

        return super(CachedReferenceField, self).__get__(instance, owner)

    def to_mongo(self, document):
        id_field_name = self.document_type._meta['id_field']
        id_field = self.document_type._fields[id_field_name]
        doc_tipe = self.document_type

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.pk
            if id_ is None:
                self.error('You can only reference documents once they have'
                           ' been saved to the database')
        else:
            self.error('Only accept a document object')

        value = SON((
            ("_id", id_field.to_mongo(id_)),
        ))

        value.update(dict(document.to_mongo(fields=self.fields)))
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None

        if isinstance(value, Document):
            if value.pk is None:
                self.error('You can only reference documents once they have'
                           ' been saved to the database')
            return {'_id': value.pk}

        raise NotImplementedError

    def validate(self, value):

        if not isinstance(value, (self.document_type)):
            self.error("A CachedReferenceField only accepts documents")

        if isinstance(value, Document) and value.id is None:
            self.error('You can only reference documents once they have been '
                       'saved to the database')

    def lookup_member(self, member_name):
        return self.document_type._fields.get(member_name)

    def sync_all(self):
        """
        Sync all cached fields on demand.
        Caution: this operation may be slower.
        """
        update_key = 'set__%s' % self.name

        for doc in self.document_type.objects:
            filter_kwargs = {}
            filter_kwargs[self.name] = doc

            update_kwargs = {}
            update_kwargs[update_key] = doc

            self.owner_document.objects(
                **filter_kwargs).update(**update_kwargs)


class GenericReferenceField(BaseField):

    """A reference to *any* :class:`~mongoengine.document.Document` subclass
    that will be automatically dereferenced on access (lazily).

    .. note ::
        * Any documents used as a generic reference must be registered in the
          document registry.  Importing the model will automatically register
          it.

        * You can use the choices param to limit the acceptable Document types

    .. versionadded:: 0.3
    """

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = instance._data.get(self.name)

        self._auto_dereference = instance._fields[self.name]._auto_dereference
        if self._auto_dereference and isinstance(value, (dict, SON)):
            instance._data[self.name] = self.dereference(value)

        return super(GenericReferenceField, self).__get__(instance, owner)

    def validate(self, value):
        if not isinstance(value, (Document, DBRef, dict, SON)):
            self.error('GenericReferences can only contain documents')

        if isinstance(value, (dict, SON)):
            if '_ref' not in value or '_cls' not in value:
                self.error('GenericReferences can only contain documents')

        # We need the id from the saved object to create the DBRef
        elif isinstance(value, Document) and value.id is None:
            self.error('You can only reference documents once they have been'
                       ' saved to the database')

    def dereference(self, value):
        doc_cls = get_document(value['_cls'])
        reference = value['_ref']
        doc = doc_cls._get_db().dereference(reference)
        if doc is not None:
            doc = doc_cls._from_son(doc)
        return doc

    def to_mongo(self, document, use_db_field=True):
        if document is None:
            return None

        if isinstance(document, (dict, SON)):
            return document

        id_field_name = document.__class__._meta['id_field']
        id_field = document.__class__._fields[id_field_name]

        if isinstance(document, Document):
            # We need the id from the saved object to create the DBRef
            id_ = document.id
            if id_ is None:
                self.error('You can only reference documents once they have'
                           ' been saved to the database')
        else:
            id_ = document

        id_ = id_field.to_mongo(id_)
        collection = document._get_collection_name()
        ref = DBRef(collection, id_)
        return SON((
            ('_cls', document._class_name),
            ('_ref', ref)
        ))

    def prepare_query_value(self, op, value):
        if value is None:
            return None

        return self.to_mongo(value)


class BinaryField(BaseField):

    """A binary data field.
    """

    def __init__(self, max_bytes=None, **kwargs):
        self.max_bytes = max_bytes
        super(BinaryField, self).__init__(**kwargs)

    def __set__(self, instance, value):
        """Handle bytearrays in python 3.1"""
        if PY3 and isinstance(value, bytearray):
            value = bin_type(value)
        return super(BinaryField, self).__set__(instance, value)

    def to_mongo(self, value):
        return Binary(value)

    def validate(self, value):
        if not isinstance(value, (bin_type, txt_type, Binary)):
            self.error("BinaryField only accepts instances of "
                       "(%s, %s, Binary)" % (
                           bin_type.__name__, txt_type.__name__))

        if self.max_bytes is not None and len(value) > self.max_bytes:
            self.error('Binary value is too long')


class GridFSError(Exception):
    pass


class GridFSProxy(object):

    """Proxy object to handle writing and reading of files to and from GridFS

    .. versionadded:: 0.4
    .. versionchanged:: 0.5 - added optional size param to read
    .. versionchanged:: 0.6 - added collection name param
    """

    _fs = None

    def __init__(self, grid_id=None, key=None,
                 instance=None,
                 db_alias=DEFAULT_CONNECTION_NAME,
                 collection_name='fs'):
        self.grid_id = grid_id                  # Store GridFS id for file
        self.key = key
        self.instance = instance
        self.db_alias = db_alias
        self.collection_name = collection_name
        self.newfile = None                     # Used for partial writes
        self.gridout = None

    def __getattr__(self, name):
        attrs = ('_fs', 'grid_id', 'key', 'instance', 'db_alias',
                 'collection_name', 'newfile', 'gridout')
        if name in attrs:
            return self.__getattribute__(name)
        obj = self.get()
        if hasattr(obj, name):
            return getattr(obj, name)
        raise AttributeError

    def __get__(self, instance, value):
        return self

    def __nonzero__(self):
        return bool(self.grid_id)

    def __getstate__(self):
        self_dict = self.__dict__
        self_dict['_fs'] = None
        return self_dict

    def __copy__(self):
        copied = GridFSProxy()
        copied.__dict__.update(self.__getstate__())
        return copied

    def __deepcopy__(self, memo):
        return self.__copy__()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.grid_id)

    def __str__(self):
        name = getattr(
            self.get(), 'filename', self.grid_id) if self.get() else '(no file)'
        return '<%s: %s>' % (self.__class__.__name__, name)

    def __eq__(self, other):
        if isinstance(other, GridFSProxy):
            return ((self.grid_id == other.grid_id) and
                    (self.collection_name == other.collection_name) and
                    (self.db_alias == other.db_alias))
        else:
            return False

    @property
    def fs(self):
        if not self._fs:
            self._fs = gridfs.GridFS(
                get_db(self.db_alias), self.collection_name)
        return self._fs

    def get(self, id=None):
        if id:
            self.grid_id = id
        if self.grid_id is None:
            return None
        try:
            if self.gridout is None:
                self.gridout = self.fs.get(self.grid_id)
            return self.gridout
        except:
            # File has been deleted
            return None

    def new_file(self, **kwargs):
        self.newfile = self.fs.new_file(**kwargs)
        self.grid_id = self.newfile._id
        self._mark_as_changed()

    def put(self, file_obj, **kwargs):
        if self.grid_id:
            raise GridFSError('This document already has a file. Either delete '
                              'it or call replace to overwrite it')
        self.grid_id = self.fs.put(file_obj, **kwargs)
        self._mark_as_changed()

    def write(self, string):
        if self.grid_id:
            if not self.newfile:
                raise GridFSError('This document already has a file. Either '
                                  'delete it or call replace to overwrite it')
        else:
            self.new_file()
        self.newfile.write(string)

    def writelines(self, lines):
        if not self.newfile:
            self.new_file()
            self.grid_id = self.newfile._id
        self.newfile.writelines(lines)

    def read(self, size=-1):
        gridout = self.get()
        if gridout is None:
            return None
        else:
            try:
                return gridout.read(size)
            except:
                return ""

    def delete(self):
        # Delete file from GridFS, FileField still remains
        self.fs.delete(self.grid_id)
        self.grid_id = None
        self.gridout = None
        self._mark_as_changed()

    def replace(self, file_obj, **kwargs):
        self.delete()
        self.put(file_obj, **kwargs)

    def close(self):
        if self.newfile:
            self.newfile.close()

    def _mark_as_changed(self):
        """Inform the instance that `self.key` has been changed"""
        if self.instance:
            self.instance._mark_as_changed(self.key)


class FileField(BaseField):

    """A GridFS storage field.

    .. versionadded:: 0.4
    .. versionchanged:: 0.5 added optional size param for read
    .. versionchanged:: 0.6 added db_alias for multidb support
    """
    proxy_class = GridFSProxy

    def __init__(self,
                 db_alias=DEFAULT_CONNECTION_NAME,
                 collection_name="fs", **kwargs):
        super(FileField, self).__init__(**kwargs)
        self.collection_name = collection_name
        self.db_alias = db_alias

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Check if a file already exists for this model
        grid_file = instance._data.get(self.name)
        if not isinstance(grid_file, self.proxy_class):
            grid_file = self.get_proxy_obj(key=self.name, instance=instance)
            instance._data[self.name] = grid_file

        if not grid_file.key:
            grid_file.key = self.name
            grid_file.instance = instance
        return grid_file

    def __set__(self, instance, value):
        key = self.name
        if ((hasattr(value, 'read') and not
             isinstance(value, GridFSProxy)) or isinstance(value, str_types)):
            # using "FileField() = file/string" notation
            grid_file = instance._data.get(self.name)
            # If a file already exists, delete it
            if grid_file:
                try:
                    grid_file.delete()
                except:
                    pass

            # Create a new proxy object as we don't already have one
            instance._data[key] = self.get_proxy_obj(
                key=key, instance=instance)
            instance._data[key].put(value)
        else:
            instance._data[key] = value

        instance._mark_as_changed(key)

    def get_proxy_obj(self, key, instance, db_alias=None, collection_name=None):
        if db_alias is None:
            db_alias = self.db_alias
        if collection_name is None:
            collection_name = self.collection_name

        return self.proxy_class(key=key, instance=instance,
                                db_alias=db_alias,
                                collection_name=collection_name)

    def to_mongo(self, value):
        # Store the GridFS file id in MongoDB
        if isinstance(value, self.proxy_class) and value.grid_id is not None:
            return value.grid_id
        return None

    def to_python(self, value):
        if value is not None:
            return self.proxy_class(value,
                                    collection_name=self.collection_name,
                                    db_alias=self.db_alias)

    def validate(self, value):
        if value.grid_id is not None:
            if not isinstance(value, self.proxy_class):
                self.error('FileField only accepts GridFSProxy values')
            if not isinstance(value.grid_id, ObjectId):
                self.error('Invalid GridFSProxy value')


class ImageGridFsProxy(GridFSProxy):

    """
    Proxy for ImageField

    versionadded: 0.6
    """

    def put(self, file_obj, **kwargs):
        """
        Insert a image in database
        applying field properties (size, thumbnail_size)
        """
        field = self.instance._fields[self.key]
        # Handle nested fields
        if hasattr(field, 'field') and isinstance(field.field, FileField):
            field = field.field

        try:
            img = Image.open(file_obj)
            img_format = img.format
        except Exception, e:
            raise ValidationError('Invalid image: %s' % e)

        # Progressive JPEG
        progressive = img.info.get('progressive') or False

        if (kwargs.get('progressive') and
                isinstance(kwargs.get('progressive'), bool) and
                img_format == 'JPEG'):
            progressive = True
        else:
            progressive = False

        if (field.size and (img.size[0] > field.size['width'] or
                            img.size[1] > field.size['height'])):
            size = field.size

            if size['force']:
                img = ImageOps.fit(img,
                                   (size['width'],
                                    size['height']),
                                   Image.ANTIALIAS)
            else:
                img.thumbnail((size['width'],
                               size['height']),
                              Image.ANTIALIAS)

        thumbnail = None
        if field.thumbnail_size:
            size = field.thumbnail_size

            if size['force']:
                thumbnail = ImageOps.fit(
                    img, (size['width'], size['height']), Image.ANTIALIAS)
            else:
                thumbnail = img.copy()
                thumbnail.thumbnail((size['width'],
                                     size['height']),
                                    Image.ANTIALIAS)

        if thumbnail:
            thumb_id = self._put_thumbnail(thumbnail, img_format, progressive)
        else:
            thumb_id = None

        w, h = img.size

        io = StringIO()
        img.save(io, img_format, progressive=progressive)
        io.seek(0)

        return super(ImageGridFsProxy, self).put(io,
                                                 width=w,
                                                 height=h,
                                                 format=img_format,
                                                 thumbnail_id=thumb_id,
                                                 **kwargs)

    def delete(self, *args, **kwargs):
        # deletes thumbnail
        out = self.get()
        if out and out.thumbnail_id:
            self.fs.delete(out.thumbnail_id)

        return super(ImageGridFsProxy, self).delete(*args, **kwargs)

    def _put_thumbnail(self, thumbnail, format, progressive, **kwargs):
        w, h = thumbnail.size

        io = StringIO()
        thumbnail.save(io, format, progressive=progressive)
        io.seek(0)

        return self.fs.put(io, width=w,
                           height=h,
                           format=format,
                           **kwargs)

    @property
    def size(self):
        """
        return a width, height of image
        """
        out = self.get()
        if out:
            return out.width, out.height

    @property
    def format(self):
        """
        return format of image
        ex: PNG, JPEG, GIF, etc
        """
        out = self.get()
        if out:
            return out.format

    @property
    def thumbnail(self):
        """
        return a gridfs.grid_file.GridOut
        representing a thumbnail of Image
        """
        out = self.get()
        if out and out.thumbnail_id:
            return self.fs.get(out.thumbnail_id)

    def write(self, *args, **kwargs):
        raise RuntimeError("Please use \"put\" method instead")

    def writelines(self, *args, **kwargs):
        raise RuntimeError("Please use \"put\" method instead")


class ImproperlyConfigured(Exception):
    pass


class ImageField(FileField):

    """
    A Image File storage field.

    @size (width, height, force):
        max size to store images, if larger will be automatically resized
        ex: size=(800, 600, True)

    @thumbnail (width, height, force):
        size to generate a thumbnail

    .. versionadded:: 0.6
    """
    proxy_class = ImageGridFsProxy

    def __init__(self, size=None, thumbnail_size=None,
                 collection_name='images', **kwargs):
        if not Image:
            raise ImproperlyConfigured("PIL library was not found")

        params_size = ('width', 'height', 'force')
        extra_args = dict(size=size, thumbnail_size=thumbnail_size)
        for att_name, att in extra_args.items():
            value = None
            if isinstance(att, (tuple, list)):
                if PY3:
                    value = dict(itertools.zip_longest(params_size, att,
                                                       fillvalue=None))
                else:
                    value = dict(map(None, params_size, att))

            setattr(self, att_name, value)

        super(ImageField, self).__init__(
            collection_name=collection_name,
            **kwargs)


class SequenceField(BaseField):

    """Provides a sequential counter see:
     http://www.mongodb.org/display/DOCS/Object+IDs#ObjectIDs-SequenceNumbers

    .. note::

             Although traditional databases often use increasing sequence
             numbers for primary keys. In MongoDB, the preferred approach is to
             use Object IDs instead.  The concept is that in a very large
             cluster of machines, it is easier to create an object ID than have
             global, uniformly increasing sequence numbers.

    Use any callable as `value_decorator` to transform calculated counter into
    any value suitable for your needs, e.g. string or hexadecimal
    representation of the default integer counter value.

    .. versionadded:: 0.5

    .. versionchanged:: 0.8 added `value_decorator`
    """

    _auto_gen = True
    COLLECTION_NAME = 'mongoengine.counters'
    VALUE_DECORATOR = int

    def __init__(self, collection_name=None, db_alias=None, sequence_name=None,
                 value_decorator=None, *args, **kwargs):
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.db_alias = db_alias or DEFAULT_CONNECTION_NAME
        self.sequence_name = sequence_name
        self.value_decorator = (callable(value_decorator) and
                                value_decorator or self.VALUE_DECORATOR)
        return super(SequenceField, self).__init__(*args, **kwargs)

    def generate(self):
        """
        Generate and Increment the counter
        """
        sequence_name = self.get_sequence_name()
        sequence_id = "%s.%s" % (sequence_name, self.name)
        collection = get_db(alias=self.db_alias)[self.collection_name]
        counter = collection.find_and_modify(query={"_id": sequence_id},
                                             update={"$inc": {"next": 1}},
                                             new=True,
                                             upsert=True)
        return self.value_decorator(counter['next'])

    def set_next_value(self, value):
        """Helper method to set the next sequence value"""
        sequence_name = self.get_sequence_name()
        sequence_id = "%s.%s" % (sequence_name, self.name)
        collection = get_db(alias=self.db_alias)[self.collection_name]
        counter = collection.find_and_modify(query={"_id": sequence_id},
                                             update={"$set": {"next": value}},
                                             new=True,
                                             upsert=True)
        return self.value_decorator(counter['next'])

    def get_next_value(self):
        """Helper method to get the next value for previewing.

        .. warning:: There is no guarantee this will be the next value
        as it is only fixed on set.
        """
        sequence_name = self.get_sequence_name()
        sequence_id = "%s.%s" % (sequence_name, self.name)
        collection = get_db(alias=self.db_alias)[self.collection_name]
        data = collection.find_one({"_id": sequence_id})

        if data:
            return self.value_decorator(data['next'] + 1)

        return self.value_decorator(1)

    def get_sequence_name(self):
        if self.sequence_name:
            return self.sequence_name
        owner = self.owner_document
        if issubclass(owner, Document):
            return owner._get_collection_name()
        else:
            return ''.join('_%s' % c if c.isupper() else c
                           for c in owner._class_name).strip('_').lower()

    def __get__(self, instance, owner):
        value = super(SequenceField, self).__get__(instance, owner)
        if value is None and instance._initialised:
            value = self.generate()
            instance._data[self.name] = value
            instance._mark_as_changed(self.name)

        return value

    def __set__(self, instance, value):

        if value is None and instance._initialised:
            value = self.generate()

        return super(SequenceField, self).__set__(instance, value)

    def prepare_query_value(self, op, value):
        """
        This method is overridden in order to convert the query value into to required
        type. We need to do this in order to be able to successfully compare query
        values passed as string, the base implementation returns the value as is.
        """
        return self.value_decorator(value)

    def to_python(self, value):
        if value is None:
            value = self.generate()
        return value


class UUIDField(BaseField):

    """A UUID field.

    .. versionadded:: 0.6
    """
    _binary = None

    def __init__(self, binary=True, **kwargs):
        """
        Store UUID data in the database

        :param binary: if False store as a string.

        .. versionchanged:: 0.8.0
        .. versionchanged:: 0.6.19
        """
        self._binary = binary
        super(UUIDField, self).__init__(**kwargs)

    def to_python(self, value):
        if not self._binary:
            original_value = value
            try:
                if not isinstance(value, basestring):
                    value = unicode(value)
                return uuid.UUID(value)
            except:
                return original_value
        return value

    def to_mongo(self, value):
        if not self._binary:
            return unicode(value)
        elif isinstance(value, basestring):
            return uuid.UUID(value)
        return value

    def prepare_query_value(self, op, value):
        if value is None:
            return None
        return self.to_mongo(value)

    def validate(self, value):
        if not isinstance(value, uuid.UUID):
            if not isinstance(value, basestring):
                value = str(value)
            try:
                value = uuid.UUID(value)
            except Exception, exc:
                self.error('Could not convert to UUID: %s' % exc)


class GeoPointField(BaseField):

    """A list storing a longitude and latitude coordinate.

    .. note:: this represents a generic point in a 2D plane and a legacy way of
        representing a geo point. It admits 2d indexes but not "2dsphere" indexes
        in MongoDB > 2.4 which are more natural for modeling geospatial points.
        See :ref:`geospatial-indexes`

    .. versionadded:: 0.4
    """

    _geo_index = pymongo.GEO2D

    def validate(self, value):
        """Make sure that a geo-value is of type (x, y)
        """
        if not isinstance(value, (list, tuple)):
            self.error('GeoPointField can only accept tuples or lists '
                       'of (x, y)')

        if not len(value) == 2:
            self.error("Value (%s) must be a two-dimensional point" %
                       repr(value))
        elif (not isinstance(value[0], (float, int)) or
              not isinstance(value[1], (float, int))):
            self.error(
                "Both values (%s) in point must be float or int" % repr(value))


class PointField(GeoJsonBaseField):

    """A GeoJSON field storing a longitude and latitude coordinate.

    The data is represented as:

    .. code-block:: js

        { "type" : "Point" ,
          "coordinates" : [x, y]}

    You can either pass a dict with the full information or a list
    to set the value.

    Requires mongodb >= 2.4

    .. versionadded:: 0.8
    """
    _type = "Point"


class LineStringField(GeoJsonBaseField):

    """A GeoJSON field storing a line of longitude and latitude coordinates.

    The data is represented as:

    .. code-block:: js

        { "type" : "LineString" ,
          "coordinates" : [[x1, y1], [x1, y1] ... [xn, yn]]}

    You can either pass a dict with the full information or a list of points.

    Requires mongodb >= 2.4

    .. versionadded:: 0.8
    """
    _type = "LineString"


class PolygonField(GeoJsonBaseField):

    """A GeoJSON field storing a polygon of longitude and latitude coordinates.

    The data is represented as:

    .. code-block:: js

        { "type" : "Polygon" ,
          "coordinates" : [[[x1, y1], [x1, y1] ... [xn, yn]],
                           [[x1, y1], [x1, y1] ... [xn, yn]]}

    You can either pass a dict with the full information or a list
    of LineStrings. The first LineString being the outside and the rest being
    holes.

    Requires mongodb >= 2.4

    .. versionadded:: 0.8
    """
    _type = "Polygon"


class MultiPointField(GeoJsonBaseField):

    """A GeoJSON field storing a list of Points.

    The data is represented as:

    .. code-block:: js

        { "type" : "MultiPoint" ,
          "coordinates" : [[x1, y1], [x2, y2]]}

    You can either pass a dict with the full information or a list
    to set the value.

    Requires mongodb >= 2.6

    .. versionadded:: 0.9
    """
    _type = "MultiPoint"


class MultiLineStringField(GeoJsonBaseField):

    """A GeoJSON field storing a list of LineStrings.

    The data is represented as:

    .. code-block:: js

        { "type" : "MultiLineString" ,
          "coordinates" : [[[x1, y1], [x1, y1] ... [xn, yn]],
                           [[x1, y1], [x1, y1] ... [xn, yn]]]}

    You can either pass a dict with the full information or a list of points.

    Requires mongodb >= 2.6

    .. versionadded:: 0.9
    """
    _type = "MultiLineString"


class MultiPolygonField(GeoJsonBaseField):

    """A GeoJSON field storing  list of Polygons.

    The data is represented as:

    .. code-block:: js

        { "type" : "MultiPolygon" ,
          "coordinates" : [[
                [[x1, y1], [x1, y1] ... [xn, yn]],
                [[x1, y1], [x1, y1] ... [xn, yn]]
            ], [
                [[x1, y1], [x1, y1] ... [xn, yn]],
                [[x1, y1], [x1, y1] ... [xn, yn]]
            ]
        }

    You can either pass a dict with the full information or a list
    of Polygons.

    Requires mongodb >= 2.6

    .. versionadded:: 0.9
    """
    _type = "MultiPolygon"
