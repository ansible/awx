"""
Test case to access the keyring from the command line
"""

import os.path

from keyring.tests.py30compat import unittest

import keyring.backend
from keyring import cli
from keyring import errors


class FakeKeyring(keyring.backend.KeyringBackend):
    PASSWORD = "GABUZOMEUH"

    def supported(self):
        return 1

    def set_password(self, service, username, password):
        pass

    def get_password(self, service, username):
        return self.PASSWORD

    def delete_password(self, service, username):
        pass

class SimpleKeyring(keyring.backend.KeyringBackend):
    """A very simple keyring"""

    def __init__(self):
        self.pwd = {}

    def supported(self):
        return 1

    def set_password(self, service, username, password):
        self.pwd[(service, username)] = password

    def get_password(self, service, username):
        try:
            return self.pwd[(service, username)]
        except KeyError:
            return None

    def delete_password(self, service, username):
        try:
            del self.pwd[(service, username)]
        except KeyError:
            raise errors.PasswordDeleteError("No key")

class CommandLineTestCase(unittest.TestCase):
    def setUp(self):
        self.old_keyring = keyring.get_keyring()

        self.cli = cli.CommandLineTool()
        self.cli.input_password = self.return_password
        self.cli.output_password = self.save_password
        self.cli.parser.error = self.mock_error
        self.cli.parser.print_help = lambda: None

        keyring.set_keyring(SimpleKeyring())

        self.password = ""
        self.password_returned = None
        self.last_error = None

    def tearDown(self):
        keyring.set_keyring(self.old_keyring)

    def return_password(self, *args, **kwargs):
        return self.password

    def save_password(self, password):
        self.password_returned = password

    def mock_error(self, error):
        self.last_error = error
        raise SystemExit()

    def test_wrong_arguments(self):
        self.assertEqual(1, self.cli.run([]))

        self.assertRaises(SystemExit, self.cli.run, ["get"])
        self.assertRaises(SystemExit, self.cli.run, ["get", "foo"])
        self.assertRaises(SystemExit, self.cli.run,
                          ["get", "foo", "bar", "baz"])

        self.assertRaises(SystemExit, self.cli.run, ["set"])
        self.assertRaises(SystemExit, self.cli.run, ["set", "foo"])
        self.assertRaises(SystemExit, self.cli.run,
                          ["set", "foo", "bar", "baz"])

        self.assertRaises(SystemExit, self.cli.run, ["foo", "bar", "baz"])

    def test_get_unexistent_password(self):
        self.assertEqual(1, self.cli.run(["get", "foo", "bar"]))
        self.assertEqual(None, self.password_returned)

    def test_set_and_get_password(self):
        self.password = "plop"
        self.assertEqual(0, self.cli.run(["set", "foo", "bar"]))
        self.assertEqual(0, self.cli.run(["get", "foo", "bar"]))
        self.assertEqual("plop", self.password_returned)

    def test_load_builtin_backend(self):
        self.assertEqual(1, self.cli.run([
            "get",
            "-b", "keyring.backends.file.PlaintextKeyring",
            "foo", "bar"]))
        backend = keyring.get_keyring()
        self.assertTrue(isinstance(backend,
                                   keyring.backends.file.PlaintextKeyring))

    def test_load_specific_backend_with_path(self):
        keyring_path = os.path.join(os.path.dirname(keyring.__file__), 'tests')
        self.assertEqual(0, self.cli.run(["get",
                                          "-b", "test_cli.FakeKeyring",
                                          "-p", keyring_path,
                                          "foo", "bar"]))

        backend = keyring.get_keyring()
        # Somehow, this doesn't work, because the full dotted name of the class
        # is not the same as the one expected :(
        #self.assertTrue(isinstance(backend, FakeKeyring))
        self.assertEqual(FakeKeyring.PASSWORD, self.password_returned)

    def test_load_wrong_keyrings(self):
        self.assertRaises(SystemExit, self.cli.run,
                          ["get", "foo", "bar",
                           "-b", "blablabla"  # ImportError
                          ])
        self.assertRaises(SystemExit, self.cli.run,
                          ["get", "foo", "bar",
                           "-b", "os.path.blabla"  # AttributeError
                          ])
        self.assertRaises(SystemExit, self.cli.run,
                          ["get", "foo", "bar",
                           "-b", "__builtin__.str"  # TypeError
                          ])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CommandLineTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest="test_suite")
