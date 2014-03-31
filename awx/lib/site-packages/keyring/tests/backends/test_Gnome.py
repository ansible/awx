import types
import sys

from ..py30compat import unittest
from ..test_backend import BackendBasicTests
from ..util import Environ, NoNoneDictMutator
from keyring.backends import Gnome


def ImportBlesser(*names, **changes):
    """A context manager to temporarily make it possible to import a module"""
    for name in names:
        changes[name] = types.ModuleType(name)
    return NoNoneDictMutator(sys.modules, **changes)


@unittest.skipUnless(Gnome.Keyring.viable, "Need GnomeKeyring")
class GnomeKeyringTestCase(BackendBasicTests, unittest.TestCase):

    def environ(self):
        return dict(DISPLAY='1',
                    DBUS_SESSION_BUS_ADDRESS='1')

    def init_keyring(self):
        k = Gnome.Keyring()

        # Store passwords in the session (in-memory) keyring for the tests. This
        # is going to be automatically cleared when the user logoff.
        k.KEYRING_NAME = 'session'

        return k

    def test_supported(self):
        with ImportBlesser('gi.repository'):
            with Environ(**self.environ()):
                self.assertTrue(Gnome.Keyring.viable)

    def test_supported_no_module(self):
        with NoNoneDictMutator(Gnome.__dict__, GnomeKeyring=None):
            with Environ(**self.environ()):
                self.assertFalse(Gnome.Keyring.viable)

    def test_supported_no_display(self):
        environ = self.environ()
        environ['DISPLAY'] = None
        with Environ(**environ):
            self.assertFalse(Gnome.Keyring.viable)

    def test_supported_no_session(self):
        environ = self.environ()
        environ['DBUS_SESSION_BUS_ADDRESS'] = None
        with Environ(**environ):
            self.assertFalse(Gnome.Keyring.viable)
