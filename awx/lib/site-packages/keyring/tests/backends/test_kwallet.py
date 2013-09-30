from ..py30compat import unittest

from keyring.backends import kwallet
from ..test_backend import BackendBasicTests

def is_qt4_supported():
    try:
        __import__('PyQt4.QtGui')
    except ImportError:
        return False
    return True

@unittest.skipUnless(kwallet.Keyring.viable, "Need KWallet")
class KDEKWalletTestCase(BackendBasicTests, unittest.TestCase):

    def init_keyring(self):
        return kwallet.Keyring()


class UnOpenableKWallet(object):
    """A module-like object used to test KDE wallet fall-back."""

    Synchronous = None

    def openWallet(self, *args):
        return None

    def NetworkWallet(self):
        return None


class FauxQtGui(object):
    """A fake module-like object used in testing the open_kwallet function."""

    class qApp:
        @staticmethod
        def instance():
            pass

    class QApplication(object):
        def __init__(self, *args):
            pass

        def exit(self):
            pass

    class QWidget(object):
        def __init__(self, *args):
            pass

        def winId(self):
            pass

class KDEWalletCanceledTestCase(unittest.TestCase):

    def test_user_canceled(self):
        # If the user cancels either the "enter your password to unlock the
        # keyring" dialog or clicks "deny" on the "can this application access
        # the wallet" dialog then openWallet() will return None.  The
        # open_wallet() function should handle that eventuality by returning
        # None to signify that the KWallet backend is not available.
        self.assertEqual(
            kwallet.open_kwallet(UnOpenableKWallet(), FauxQtGui()),
            None)


@unittest.skipUnless(kwallet.Keyring.viable and
                     is_qt4_supported(),
                     "Need KWallet and Qt4")
class KDEKWalletInQApplication(unittest.TestCase):
    def test_QApplication(self):
        try:
            from PyKDE4.kdeui import KWallet
            from PyQt4.QtGui import QApplication
        except:
            return

        app = QApplication([])
        wallet = kwallet.open_kwallet()
        self.assertTrue(isinstance(wallet, KWallet.Wallet),
                        msg="The object wallet should be type "
                        "<KWallet.Wallet> but it is: %s" % repr(wallet))
        app.exit()
