import six
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django import forms
from django.conf import settings
import warnings

try:
    from keyczar import keyczar
except ImportError:
    raise ImportError('Using an encrypted field requires the Keyczar module. '
                      'You can obtain Keyczar from http://www.keyczar.org/.')


class EncryptionWarning(RuntimeWarning):
    pass


class BaseEncryptedField(models.Field):
    prefix = 'enc_str:::'

    def __init__(self, *args, **kwargs):
        if not hasattr(settings, 'ENCRYPTED_FIELD_KEYS_DIR'):
            raise ImproperlyConfigured('You must set the settings.ENCRYPTED_FIELD_KEYS_DIR '
                                       'setting to your Keyczar keys directory.')
        crypt_class = self.get_crypt_class()
        self.crypt = crypt_class.Read(settings.ENCRYPTED_FIELD_KEYS_DIR)

        # Encrypted size is larger than unencrypted
        self.unencrypted_length = max_length = kwargs.get('max_length', None)
        if max_length:
            max_length = len(self.prefix) + len(self.crypt.Encrypt('x' * max_length))
            # TODO: Re-examine if this logic will actually make a large-enough
            # max-length for unicode strings that have non-ascii characters in them.
            kwargs['max_length'] = max_length

        super(BaseEncryptedField, self).__init__(*args, **kwargs)

    def get_crypt_class(self):
        """
        Get the Keyczar class to use.

        The class can be customized with the ENCRYPTED_FIELD_MODE setting. By default,
        this setting is DECRYPT_AND_ENCRYPT. Set this to ENCRYPT to disable decryption.
        This is necessary if you are only providing public keys to Keyczar.

        Returns:
            keyczar.Encrypter if ENCRYPTED_FIELD_MODE is ENCRYPT.
            keyczar.Crypter if ENCRYPTED_FIELD_MODE is DECRYPT_AND_ENCRYPT.

        Override this method to customize the type of Keyczar class returned.
        """

        crypt_type = getattr(settings, 'ENCRYPTED_FIELD_MODE', 'DECRYPT_AND_ENCRYPT')
        if crypt_type == 'ENCRYPT':
            crypt_class_name = 'Encrypter'
        elif crypt_type == 'DECRYPT_AND_ENCRYPT':
            crypt_class_name = 'Crypter'
        else:
            raise ImproperlyConfigured(
                'ENCRYPTED_FIELD_MODE must be either DECRYPT_AND_ENCRYPT '
                'or ENCRYPT, not %s.' % crypt_type)
        return getattr(keyczar, crypt_class_name)

    def to_python(self, value):
        if isinstance(self.crypt.primary_key, keyczar.keys.RsaPublicKey):
            retval = value
        elif value and (value.startswith(self.prefix)):
            if hasattr(self.crypt, 'Decrypt'):
                retval = self.crypt.Decrypt(value[len(self.prefix):])
                if retval:
                    retval = retval.decode('utf-8')
            else:
                retval = value
        else:
            retval = value
        return retval

    def get_db_prep_value(self, value, connection, prepared=False):
        if value and not value.startswith(self.prefix):
            # We need to encode a unicode string into a byte string, first.
            # keyczar expects a bytestring, not a unicode string.
            if type(value) == six.types.UnicodeType:
                value = value.encode('utf-8')
            # Truncated encrypted content is unreadable,
            # so truncate before encryption
            max_length = self.unencrypted_length
            if max_length and len(value) > max_length:
                warnings.warn("Truncating field %s from %d to %d bytes" % (
                    self.name, len(value), max_length), EncryptionWarning
                )
                value = value[:max_length]

            value = self.prefix + self.crypt.Encrypt(value)
        return value


class EncryptedTextField(six.with_metaclass(models.SubfieldBase,
                                            BaseEncryptedField)):
    def get_internal_type(self):
        return 'TextField'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super(EncryptedTextField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)


class EncryptedCharField(six.with_metaclass(models.SubfieldBase,
                                            BaseEncryptedField)):
    def __init__(self, *args, **kwargs):
        super(EncryptedCharField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super(EncryptedCharField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
