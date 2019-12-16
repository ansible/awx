# -*- coding: utf-8 -*-

import base64
import hashlib
import logging
from collections import namedtuple

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from django.utils.encoding import smart_str, smart_bytes


__all__ = ['get_encryption_key',
           'encrypt_field', 'decrypt_field',
           'encrypt_value', 'decrypt_value',
           'encrypt_dict']

logger = logging.getLogger('awx.main.utils.encryption')


class Fernet256(Fernet):
    '''Not techincally Fernet, but uses the base of the Fernet spec and uses AES-256-CBC
    instead of AES-128-CBC. All other functionality remain identical.
    '''
    def __init__(self, key, backend=None):
        if backend is None:
            backend = default_backend()

        key = base64.urlsafe_b64decode(key)
        if len(key) != 64:
            raise ValueError(
                "Fernet key must be 64 url-safe base64-encoded bytes."
            )

        self._signing_key = key[:32]
        self._encryption_key = key[32:]
        self._backend = backend


def get_encryption_key(field_name, pk=None, secret_key=None):
    '''
    Generate key for encrypted password based on field name,
    ``settings.SECRET_KEY``, and instance pk (if available).

    :param pk: (optional) the primary key of the model object;
               can be omitted in situations where you're encrypting a setting
               that is not database-persistent (like a read-only setting)
    '''
    from django.conf import settings
    h = hashlib.sha512()
    h.update(smart_bytes(secret_key or settings.SECRET_KEY))
    if pk is not None:
        h.update(smart_bytes(str(pk)))
    h.update(smart_bytes(field_name))
    return base64.urlsafe_b64encode(h.digest())


def encrypt_value(value, pk=None, secret_key=None):
    #
    # ⚠️  D-D-D-DANGER ZONE ⚠️
    #
    # !!! BEFORE USING THIS FUNCTION PLEASE READ encrypt_field !!!
    #
    TransientField = namedtuple('TransientField', ['pk', 'value'])
    return encrypt_field(TransientField(pk=pk, value=value), 'value', secret_key=secret_key)


def encrypt_field(instance, field_name, ask=False, subfield=None, secret_key=None):
    #
    # ⚠️  D-D-D-DANGER ZONE ⚠️
    #
    # !!! PLEASE READ BEFORE USING THIS FUNCTION ANYWHERE !!!
    #
    # You should know that this function is used in various places throughout
    # AWX for symmetric encryption - generally it's used to encrypt sensitive
    # values that we store in the AWX database (such as SSH private keys for
    # credentials).
    #
    # If you're reading this function's code because you're thinking about
    # using it to encrypt *something new*, please remember that AWX has
    # official support for *regenerating* the SECRET_KEY (on which the
    # symmetric key is based):
    #
    # $ awx-manage regenerate_secret_key
    # $ setup.sh -k
    #
    # ...so you'll need to *also* add code to support the
    # migration/re-encryption of these values (the code in question lives in
    # `awx.main.management.commands.regenerate_secret_key`):
    #
    # For example, if you find that you're adding a new database column that is
    # encrypted, in addition to calling `encrypt_field` in the appropriate
    # places, you would also need to update the `awx-manage regenerate_secret_key`
    # so that values are properly migrated when the SECRET_KEY changes.
    #
    # This process *generally* involves adding Python code to the
    # `regenerate_secret_key` command, i.e.,
    #
    # 1.  Query the database for existing encrypted values on the appropriate object(s)
    # 2.  Decrypting them using the *old* SECRET_KEY
    # 3.  Storing newly encrypted values using the *newly generated* SECRET_KEY
    #
    '''
    Return content of the given instance and field name encrypted.
    '''
    try:
        value = instance.inputs[field_name]
    except (TypeError, AttributeError):
        value = getattr(instance, field_name)
    except KeyError:
        raise AttributeError(field_name)

    if isinstance(value, dict) and subfield is not None:
        value = value[subfield]
    if value is None:
        return None
    value = smart_str(value)
    if not value or value.startswith('$encrypted$') or (ask and value == 'ASK'):
        return value
    key = get_encryption_key(
        field_name,
        getattr(instance, 'pk', None),
        secret_key=secret_key
    )
    f = Fernet256(key)
    encrypted = f.encrypt(smart_bytes(value))
    b64data = smart_str(base64.b64encode(encrypted))
    tokens = ['$encrypted', 'UTF8', 'AESCBC', b64data]
    return '$'.join(tokens)


def decrypt_value(encryption_key, value):
    raw_data = value[len('$encrypted$'):]
    # If the encrypted string contains a UTF8 marker, discard it
    utf8 = raw_data.startswith('UTF8$')
    if utf8:
        raw_data = raw_data[len('UTF8$'):]
    algo, b64data = raw_data.split('$', 1)
    if algo != 'AESCBC':
        raise ValueError('unsupported algorithm: %s' % algo)
    encrypted = base64.b64decode(b64data)
    f = Fernet256(encryption_key)
    value = f.decrypt(encrypted)
    return smart_str(value)


def decrypt_field(instance, field_name, subfield=None, secret_key=None):
    '''
    Return content of the given instance and field name decrypted.
    '''
    try:
        value = instance.inputs[field_name]
    except (TypeError, AttributeError):
        value = getattr(instance, field_name)
    except KeyError:
        raise AttributeError(field_name)

    if isinstance(value, dict) and subfield is not None:
        value = value[subfield]
    value = smart_str(value)
    if not value or not value.startswith('$encrypted$'):
        return value
    key = get_encryption_key(
        field_name,
        getattr(instance, 'pk', None),
        secret_key=secret_key
    )

    try:
        return smart_str(decrypt_value(key, value))
    except InvalidToken:
        logger.exception(
            "Failed to decrypt `%s(pk=%s).%s`; if you've recently restored from "
            "a database backup or are running in a clustered environment, "
            "check that your `SECRET_KEY` value is correct",
            instance.__class__.__name__,
            getattr(instance, 'pk', None),
            field_name,
            exc_info=True
        )
        raise


def encrypt_dict(data, fields):
    '''
    Encrypts all of the dictionary values in `data` under the keys in `fields`
    in-place operation on `data`
    '''
    encrypt_fields = set(data.keys()).intersection(fields)
    for key in encrypt_fields:
        data[key] = encrypt_value(data[key])


def is_encrypted(value):
    if not isinstance(value, str):
        return False
    return value.startswith('$encrypted$') and len(value) > len('$encrypted$')
