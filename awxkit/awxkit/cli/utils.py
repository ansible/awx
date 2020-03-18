from __future__ import print_function

from argparse import ArgumentParser
import os
import sys
import threading

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
    'canceled': 'grey',
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


COLORS = dict(
    list(
        zip(
            [
                'grey', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan',
                'white',
            ],
            list(range(30, 38))
        )
    )
)


def colored(text, color=None):
    '''Colorize text w/ ANSI color sequences'''
    if _color.enabled and os.getenv('ANSI_COLORS_DISABLED') is None:
        fmt_str = '\033[%dm%s'
        if color is not None:
            text = fmt_str % (COLORS[color], text)
        text += '\033[0m'
    return text


def cprint(text, color, **kwargs):
    if _color.enabled:
        print(colored(text, color), **kwargs)
    else:
        print(text, **kwargs)
