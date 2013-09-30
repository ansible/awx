import os
import tempfile

from ..py30compat import unittest

import keyring.backend
from keyring.backends import pyfs
from ..test_backend import BackendBasicTests, random_string


class ReverseCrypter(keyring.backend.Crypter):
    """Very silly crypter class"""

    def encrypt(self, value):
        return value[::-1]

    def decrypt(self, value):
        return value[::-1]

class PyfilesystemKeyringTests(BackendBasicTests):
    """Base class for Pyfilesystem tests"""

    def setUp(self):
        super(PyfilesystemKeyringTests, self).setUp()
        self.keyring = self.init_keyring()

    def tearDown(self):
        del self.keyring

    def test_encrypt_decrypt(self):
        password = random_string(20)
        encrypted = self.keyring.encrypt(password)

        self.assertEqual(password, self.keyring.decrypt(encrypted))

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class UnencryptedMemoryPyfilesystemKeyringNoSubDirTestCase(
        PyfilesystemKeyringTests, unittest.TestCase):
    """Test in memory with no encryption"""

    keyring_filename = 'mem://unencrypted'

    def init_keyring(self):
        return keyring.backends.pyfs.PlaintextKeyring(
            filename=self.keyring_filename)

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class UnencryptedMemoryPyfilesystemKeyringSubDirTestCase(
        PyfilesystemKeyringTests, unittest.TestCase):
    """Test in memory with no encryption"""

    keyring_filename = 'mem://some/sub/dir/unencrypted'

    def init_keyring(self):
        return keyring.backends.pyfs.PlaintextKeyring(
            filename=self.keyring_filename)

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class UnencryptedLocalPyfilesystemKeyringNoSubDirTestCase(
        PyfilesystemKeyringTests, unittest.TestCase):
    """Test using local temp files with no encryption"""

    keyring_filename = '%s/keyring.cfg' %tempfile.mkdtemp()

    def init_keyring(self):
        return keyring.backends.pyfs.PlaintextKeyring(
            filename=self.keyring_filename)

    def test_handles_preexisting_keyring(self):
        from fs.opener import opener
        fs, path = opener.parse(self.keyring_filename, writeable=True)
        keyring_file = fs.open(path, 'wb')
        keyring_file.write(
            """[svc1]
user1 = cHdkMQ==
            """)
        keyring_file.close()
        pyf_keyring = keyring.backends.pyfs.PlaintextKeyring(
            filename=self.keyring_filename)
        self.assertEquals('pwd1', pyf_keyring.get_password('svc1', 'user1'))

    def tearDown(self):
        del self.keyring
        if os.path.exists(self.keyring_filename):
            os.remove(self.keyring_filename)

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class UnencryptedLocalPyfilesystemKeyringSubDirTestCase(
        PyfilesystemKeyringTests, unittest.TestCase):
    """Test using local temp files with no encryption"""

    keyring_dir = os.path.join(tempfile.mkdtemp(), 'more', 'sub', 'dirs')
    keyring_filename = os.path.join(keyring_dir, 'keyring.cfg')

    def init_keyring(self):

        if not os.path.exists(self.keyring_dir):
            os.makedirs(self.keyring_dir)
        return keyring.backends.pyfs.PlaintextKeyring(
            filename=self.keyring_filename)

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class EncryptedMemoryPyfilesystemKeyringTestCase(PyfilesystemKeyringTests,
        unittest.TestCase):
    """Test in memory with encryption"""

    def init_keyring(self):
        return keyring.backends.pyfs.EncryptedKeyring(
            ReverseCrypter(),
            filename='mem://encrypted/keyring.cfg')

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class EncryptedLocalPyfilesystemKeyringNoSubDirTestCase(
        PyfilesystemKeyringTests, unittest.TestCase):
    """Test using local temp files with encryption"""

    def init_keyring(self):
        return keyring.backends.pyfs.EncryptedKeyring(
            ReverseCrypter(),
            filename='temp://keyring.cfg')

@unittest.skipUnless(pyfs.BasicKeyring.viable, "Need Pyfilesystem")
class EncryptedLocalPyfilesystemKeyringSubDirTestCase(
        PyfilesystemKeyringTests, unittest.TestCase):
    """Test using local temp files with encryption"""

    def init_keyring(self):
        return keyring.backends.pyfs.EncryptedKeyring(
            ReverseCrypter(),
            filename='temp://a/sub/dir/hierarchy/keyring.cfg')
