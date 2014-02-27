# -*- coding: utf-8 -*-

####################################################################

import uuid

from django import forms
from django.db import models
from django.utils.encoding import smart_text
from django.utils import six

class UUIDVersionError(Exception):
    pass


class UUIDField(six.with_metaclass(models.SubfieldBase, models.CharField)):
    """Encode and stores a Python uuid.UUID in a manner that is appropriate
    for the given datatabase that we are using.

    For sqlite3 or MySQL we save it as a 36-character string value
    For PostgreSQL we save it as a uuid field

    This class supports type 1, 2, 4, and 5 UUID's.
    """

    _CREATE_COLUMN_TYPES = {
        'postgresql_psycopg2': 'uuid',
        'postgresql': 'uuid'
    }

    def __init__(self, verbose_name=None, name=None, auto=True, version=1, node=None, clock_seq=None, namespace=None, **kwargs):
        """Contruct a UUIDField.

        @param verbose_name: Optional verbose name to use in place of what
            Django would assign.
        @param name: Override Django's name assignment
        @param auto: If True, create a UUID value if one is not specified.
        @param version: By default we create a version 1 UUID.
        @param node: Used for version 1 UUID's. If not supplied, then the uuid.getnode() function is called to obtain it. This can be slow.
        @param clock_seq: Used for version 1 UUID's. If not supplied a random 14-bit sequence number is chosen
        @param namespace: Required for version 3 and version 5 UUID's.
        @param name: Required for version4 and version 5 UUID's.

        See Also:
          - Python Library Reference, section 18.16 for more information.
          - RFC 4122, "A Universally Unique IDentifier (UUID) URN Namespace"

        If you want to use one of these as a primary key for a Django
        model, do this::
            id = UUIDField(primary_key=True)
        This will currently I{not} work with Jython because PostgreSQL support
        in Jython is not working for uuid column types.
        """
        self.max_length = 36
        kwargs['max_length'] = self.max_length
        if auto:
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)

        self.auto = auto
        self.version = version
        if version == 1:
            self.node, self.clock_seq = node, clock_seq
        elif version == 3 or version == 5:
            self.namespace, self.name = namespace, name

        super(UUIDField, self).__init__(verbose_name=verbose_name,
            name=name, **kwargs)

    def create_uuid(self):
        if not self.version or self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)

    def db_type(self, connection):
        from django.conf import settings
        full_database_type = settings.DATABASES['default']['ENGINE']
        database_type = full_database_type.split('.')[-1]
        return UUIDField._CREATE_COLUMN_TYPES.get(database_type, "char(%s)" % self.max_length)

    def to_python(self, value):
        """Return a uuid.UUID instance from the value returned by the database."""
        #
        # This is the proper way... But this doesn't work correctly when
        # working with an inherited model
        #
        if not value:
            return None
        if isinstance(value, uuid.UUID):
            return value
        # attempt to parse a UUID
        return uuid.UUID(smart_text(value))

        #
        # If I do the following (returning a String instead of a UUID
        # instance), everything works.
        #

        #if not value:
        # return None
        #if isinstance(value, uuid.UUID):
        # return smart_text(value)
        #else:
        # return value

    def pre_save(self, model_instance, add):
        if self.auto and add:
            value = self.create_uuid()
            setattr(model_instance, self.attname, value)
        else:
            value = super(UUIDField, self).pre_save(model_instance, add)
            if self.auto and not value:
                value = self.create_uuid()
                setattr(model_instance, self.attname, value)
        return value

    def get_db_prep_value(self, value, connection, prepared):
        """Casts uuid.UUID values into the format expected by the back end for use in queries"""
        if isinstance(value, uuid.UUID):
            return smart_text(value)
        return value

    def value_to_string(self, obj):
        val = self._get_val_from_obj(obj)
        if val is None:
            data = ''
        else:
            data = smart_text(val)
        return data

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.CharField,
            'max_length': self.max_length
            }
        defaults.update(kwargs)
        return super(UUIDField, self).formfield(**defaults)
