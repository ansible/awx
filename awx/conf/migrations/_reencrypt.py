import base64
import hashlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import ECB


__all__ = ['get_encryption_key', 'decrypt_field']


def get_encryption_key(field_name, pk=None):
    '''
    Generate key for encrypted password based on field name,
    ``settings.SECRET_KEY``, and instance pk (if available).

    :param pk: (optional) the primary key of the ``awx.conf.model.Setting``;
               can be omitted in situations where you're encrypting a setting
               that is not database-persistent (like a read-only setting)
    '''
    from django.conf import settings
    h = hashlib.sha1()
    h.update(settings.SECRET_KEY)
    if pk is not None:
        h.update(str(pk))
    h.update(field_name)
    return h.digest()[:16]


def decrypt_value(encryption_key, value):
    raw_data = value[len('$encrypted$'):]
    # If the encrypted string contains a UTF8 marker, discard it
    utf8 = raw_data.startswith('UTF8$')
    if utf8:
        raw_data = raw_data[len('UTF8$'):]
    algo, b64data = raw_data.split('$', 1)
    if algo != 'AES':
        raise ValueError('unsupported algorithm: %s' % algo)
    encrypted = base64.b64decode(b64data)
    decryptor = Cipher(AES(encryption_key), ECB(), default_backend()).decryptor()
    value = decryptor.update(encrypted) + decryptor.finalize()
    value = value.rstrip('\x00')
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

    return decrypt_value(key, value)
