#!/usr/bin/env python
"""Simple command line interface to get/set password from a keyring"""

import getpass
from optparse import OptionParser
import sys

import keyring
import keyring.core


class CommandLineTool(object):
    def __init__(self):
        self.parser = OptionParser(
                        usage="%prog [get|set|del] SERVICE USERNAME")
        self.parser.add_option("-p", "--keyring-path",
                               dest="keyring_path", default=None,
                               help="Path to the keyring backend")
        self.parser.add_option("-b", "--keyring-backend",
                               dest="keyring_backend", default=None,
                               help="Name of the keyring backend")

    def run(self, argv):
        opts, args = self.parser.parse_args(argv)

        try:
            kind, service, username = args
        except ValueError:
            if len(args) == 0:
                # Be nice with the user if he just tries to launch the tool
                self.parser.print_help()
                return 1
            else:
                self.parser.error("Wrong number of arguments")

        if opts.keyring_backend is not None:
            try:
                backend = keyring.core.load_keyring(opts.keyring_path,
                                                    opts.keyring_backend)
                keyring.set_keyring(backend)
            except (Exception,):
                # Tons of things can go wrong here:
                #   ImportError when using "fjkljfljkl"
                #   AttributeError when using "os.path.bar"
                #   TypeError when using "__builtins__.str"
                # So, we play on the safe side, and catch everything.
                e = sys.exc_info()[1]
                self.parser.error("Unable to load specified keyring: %s" % e)

        if kind == 'get':
            password = keyring.get_password(service, username)
            if password is None:
                return 1

            self.output_password(password)
            return 0

        elif kind == 'set':
            password = self.input_password("Password for '%s' in '%s': " %
                                           (username, service))
            keyring.set_password(service, username, password)
            return 0

        elif kind == 'del':
            password = self.input_password("Deleting password for '%s' in '%s': " %
                                      (username, service))
            keyring.delete_password(service, username)
            return 0

        else:
            self.parser.error("You can only 'get', 'del' or 'set' a password.")
            pass

    def input_password(self, prompt):
        """Ask for a password to the user.

        This mostly exists to ease the testing process.
        """

        return getpass.getpass(prompt)

    def output_password(self, password):
        """Output the password to the user.

        This mostly exists to ease the testing process.
        """

        print >> sys.stdout, password


def main(argv=None):
    """Main command line interface."""

    if argv is None:
        argv = sys.argv[1:]

    cli = CommandLineTool()
    return cli.run(argv)


if __name__ == '__main__':
    sys.exit(main())
