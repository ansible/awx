#!/usr/bin/env python
"""Simple command line interface to get/set password from a keyring"""

from __future__ import print_function

import getpass
from optparse import OptionParser
import sys

from . import get_keyring, set_keyring, get_password, set_password, delete_password
from . import core


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
                if opts.keyring_path:
                    sys.path.insert(0, opts.keyring_path)
                backend = core.load_keyring(opts.keyring_backend)
                set_keyring(backend)
            except (Exception,):
                # Tons of things can go wrong here:
                #   ImportError when using "fjkljfljkl"
                #   AttributeError when using "os.path.bar"
                #   TypeError when using "__builtins__.str"
                # So, we play on the safe side, and catch everything.
                e = sys.exc_info()[1]
                self.parser.error("Unable to load specified keyring: %s" % e)

        if kind == 'get':
            password = get_password(service, username)
            if password is None:
                return 1

            self.output_password(password)
            return 0

        elif kind == 'set':
            password = self.input_password("Password for '%s' in '%s': " %
                                           (username, service))
            set_password(service, username, password)
            return 0

        elif kind == 'del':
            password = self.input_password("Deleting password for '%s' in '%s': " %
                                      (username, service))
            delete_password(service, username)
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

        print(password, file=sys.stdout)


def main(argv=None):
    """Main command line interface."""

    if argv is None:
        argv = sys.argv[1:]

    cli = CommandLineTool()
    return cli.run(argv)


if __name__ == '__main__':
    sys.exit(main())
