import base64
import hashlib
import logging

import six
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from django.utils.encoding import smart_str


__all__ = ['get_encryption_key', 'encrypt_field', 'decrypt_field', 'decrypt_value']

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


def get_encryption_key(field_name, pk=None):
    '''
    Generate key for encrypted password based on field name,
    ``settings.SECRET_KEY``, and instance pk (if available).

    :param pk: (optional) the primary key of the model object;
               can be omitted in situations where you're encrypting a setting
               that is not database-persistent (like a read-only setting)
    '''
    from django.conf import settings
    h = hashlib.sha512()
    h.update(settings.SECRET_KEY)
    if pk is not None:
        h.update(str(pk))
    h.update(field_name)
    return base64.urlsafe_b64encode(h.digest())


def encrypt_field(instance, field_name, ask=False, subfield=None, skip_utf8=False):
    '''
    Return content of the given instance and field name encrypted.
    '''
    value = getattr(instance, field_name)
    if isinstance(value, dict) and subfield is not None:
        value = value[subfield]
    if not value or value.startswith('$encrypted$') or (ask and value == 'ASK'):
        return value
    if skip_utf8:
        utf8 = False
    else:
        utf8 = type(value) == six.text_type
    value = smart_str(value)
    key = get_encryption_key(field_name, getattr(instance, 'pk', None))
    f = Fernet256(key)
    encrypted = f.encrypt(value)
    b64data = base64.b64encode(encrypted)
    tokens = ['$encrypted', 'AESCBC', b64data]
    if utf8:
        # If the value to encrypt is utf-8, we need to add a marker so we
        # know to decode the data when it's decrypted later
        tokens.insert(1, 'UTF8')
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
    # If the encrypted string contained a UTF8 marker, decode the data
    if utf8:
        value = value.decode('utf-8')
    return value


def decrypt_field(instance, field_name, subfield=None):
    '''
    Return content of the given instance and field name decrypted.
    '''
    value = getattr(instance, field_name)
    if isinstance(value, dict) and subfield is not None:
        value = value[subfield]
    if not value or not value.startswith('$encrypted$'):
        return value
    key = get_encryption_key(field_name, getattr(instance, 'pk', None))

    try:
        return decrypt_value(key, value)
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
