from argparse import ArgumentParser
import threading
import sys

import termcolor

_color = threading.local()
_color.enabled = True


__all__ = ['CustomRegistryMeta', 'HelpfulArgumentParser', 'disable_color',
           'color_enabled', 'colored', 'cprint', 'STATUS_COLORS']


STATUS_COLORS = {
    'new': 'grey',
    'pending': 'grey',
    'running': 'yellow',
    'successful': 'green',
    'failed': 'red',
    'error': 'red',
    'cancelled': 'grey',
}


class CustomRegistryMeta(type):

    @property
    def registry(cls):
        return dict(
            (command.name, command)
            for command in cls.__subclasses__()
        )


class HelpfulArgumentParser(ArgumentParser):

    def error(self, message):  # pragma: nocover
        """Prints a usage message incorporating the message to stderr and
        exits.
        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        self.print_help(sys.stderr)
        self._print_message('\n')
        self.exit(2, '%s: %s\n' % (self.prog, message))

    def _parse_known_args(self, args, ns):
        for arg in ('-h', '--help'):
            # the -h argument is extraneous; if you leave it off,
            # awx-cli will just print usage info
            if arg in args:
                args.remove(arg)
        return super(HelpfulArgumentParser, self)._parse_known_args(args, ns)


def color_enabled():
    return _color.enabled


def disable_color():
    _color.enabled = False


def colored(value, color):
    if _color.enabled:
        return termcolor.colored(value, color)
    else:
        return value


def cprint(value, color, **kwargs):
    if _color.enabled:
        termcolor.cprint(value, color, **kwargs)
    else:
        print(value, **kwargs)
