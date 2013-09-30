from __future__ import absolute_import

import os
import abc

try:
    from keyczar import keyczar
except ImportError:
    pass

from keyring.backend import Crypter
from keyring import errors

def has_keyczar():
    with errors.ExceptionRaisedContext() as exc:
        keyczar.__name__
    return not bool(exc)

class BaseCrypter(Crypter):
    """Base Keyczar keyset encryption and decryption.
       The keyset initialisation is deferred until required.
    """

    @abc.abstractproperty
    def keyset_location(self):
        """Location for the main keyset that may be encrypted or not"""
        pass

    @abc.abstractproperty
    def encrypting_keyset_location(self):
        """Location for the encrypting keyset.
           Use None to indicate that the main keyset is not encrypted
        """
        pass

    @property
    def crypter(self):
        """The actual keyczar crypter"""
        if not hasattr(self, '_crypter'):
            # initialise the Keyczar keysets
            if not self.keyset_location:
                raise ValueError('No encrypted keyset location!')
            reader = keyczar.readers.CreateReader(self.keyset_location)
            if self.encrypting_keyset_location:
                encrypting_keyczar = keyczar.Crypter.Read(
                    self.encrypting_keyset_location)
                reader = keyczar.readers.EncryptedReader(reader,
                                                         encrypting_keyczar)
            self._crypter = keyczar.Crypter(reader)
        return self._crypter

    def encrypt(self, value):
        """Encrypt the value.
        """
        if not value:
            return ''
        return self.crypter.Encrypt(value)

    def decrypt(self, value):
        """Decrypt the value.
        """
        if not value:
            return ''
        return self.crypter.Decrypt(value)

class Crypter(BaseCrypter):
    """A Keyczar crypter using locations specified in the constructor
    """

    def __init__(self, keyset_location, encrypting_keyset_location=None):
        self._keyset_location = keyset_location
        self._encrypting_keyset_location = encrypting_keyset_location

    @property
    def keyset_location(self):
        return self._keyset_location

    @property
    def encrypting_keyset_location(self):
        return self._encrypting_keyset_location

class EnvironCrypter(BaseCrypter):
    """A Keyczar crypter using locations specified by environment vars
    """

    KEYSET_ENV_VAR = 'KEYRING_KEYCZAR_ENCRYPTED_LOCATION'
    ENC_KEYSET_ENV_VAR = 'KEYRING_KEYCZAR_ENCRYPTING_LOCATION'

    @property
    def keyset_location(self):
        val = os.environ.get(self.KEYSET_ENV_VAR)
        if not val:
            raise ValueError('%s environment value not set' %
                             self.KEYSET_ENV_VAR)
        return val

    @property
    def encrypting_keyset_location(self):
        return os.environ.get(self.ENC_KEYSET_ENV_VAR)
