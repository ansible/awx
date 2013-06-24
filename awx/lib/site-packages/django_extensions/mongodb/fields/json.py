"""
JSONField automatically serializes most Python terms to JSON data.
Creates a TEXT field with a default value of "{}".  See test_json.py for
more information.

 from django.db import models
 from django_extensions.db.fields import json

 class LOL(models.Model):
     extra = json.JSONField()
"""

import six
import datetime
from decimal import Decimal
from django.conf import settings
from django.utils import simplejson
from mongoengine.fields import StringField


class JSONEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            assert settings.TIME_ZONE == 'UTC'
            return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        return simplejson.JSONEncoder.default(self, obj)


def dumps(value):
    assert isinstance(value, dict)
    return JSONEncoder().encode(value)


def loads(txt):
    value = simplejson.loads(txt, parse_float=Decimal, encoding=settings.DEFAULT_CHARSET)
    assert isinstance(value, dict)
    return value


class JSONDict(dict):
    """
    Hack so repr() called by dumpdata will output JSON instead of
    Python formatted data.  This way fixtures will work!
    """
    def __repr__(self):
        return dumps(self)


class JSONField(StringField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.  Main thingy must be a dict object."""

    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = '{}'
        StringField.__init__(self, *args, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if not value:
            return {}
        elif isinstance(value, six.string_types):
            res = loads(value)
            assert isinstance(res, dict)
            return JSONDict(**res)
        else:
            return value

    def get_db_prep_save(self, value):
        """Convert our JSON object to a string before we save"""
        if not value:
            return super(JSONField, self).get_db_prep_save("")
        else:
            return super(JSONField, self).get_db_prep_save(dumps(value))

