import sys

from ..py30compat import unittest

import keyring.backends.Windows
from ..test_backend import BackendBasicTests
from .test_file import FileKeyringTests

def is_win32_crypto_supported():
    try:
        __import__('keyring.backends._win_crypto')
    except ImportError:
        return False
    return sys.platform in ['win32'] and sys.getwindowsversion()[-2] == 2

def is_winvault_supported():
    try:
        __import__('win32cred')
        has_pywin32 = True
    except ImportError:
        has_pywin32 = False
    return (
        sys.platform in ['win32'] and sys.getwindowsversion().major >= 6
        and has_pywin32
    )


@unittest.skipUnless(is_win32_crypto_supported(),
                     "Need Windows")
class Win32CryptoKeyringTestCase(FileKeyringTests, unittest.TestCase):

    def init_keyring(self):
        return keyring.backends.Windows.EncryptedKeyring()


@unittest.skipUnless(is_winvault_supported(),
                     "Need WinVault")
class WinVaultKeyringTestCase(BackendBasicTests, unittest.TestCase):
    def tearDown(self):
        # clean up any credentials created
        for cred in self.credentials_created:
            try:
                self.keyring.delete_password(*cred)
            except (Exception,):
                e = sys.exc_info()[1]
                print >> sys.stderr, e

    def init_keyring(self):
        return keyring.backends.Windows.WinVaultKeyring()


@unittest.skipUnless(keyring.backends.Windows.RegistryKeyring.viable
    and sys.version_info > (3,), "RegistryKeyring not viable")
class RegistryKeyringTestCase(BackendBasicTests, unittest.TestCase):
    def tearDown(self):
        # clean up any credentials created
        for cred in self.credentials_created:
            try:
                self.keyring.delete_password(*cred)
            except (Exception,):
                e = sys.exc_info()[1]
                print >> sys.stderr, e

    def init_keyring(self):
        return keyring.backends.Windows.RegistryKeyring()
