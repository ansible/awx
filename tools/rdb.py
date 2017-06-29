import rlcompleter
try:
    import readline
except ImportError:
    print("Module readline not available.")
else:
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

import sys
from celery.contrib.rdb import Rdb

import cmd
import contextlib
import logging
import os
import pprint
import re
import select
import socket
import threading
from cStringIO import StringIO
from Queue import Queue, Empty

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter

logger = logging.getLogger('awx')


@contextlib.contextmanager
def style(im_self, filepart=None, lexer=None):

    lexer = PythonLexer
    old_stdout = im_self.stdout
    buff = StringIO()
    im_self.stdout = buff
    yield

    value = buff.getvalue()
    context = len(value.splitlines())
    file_cache = {}

    if filepart:
        filepath, lineno = filepart
        if filepath not in file_cache:
            with open(filepath, 'r') as source:
                file_cache[filepath] = source.readlines()
        value = ''.join(file_cache[filepath][:lineno - 1]) + value

    formatter = Terminal256Formatter(style='friendly')
    value = highlight(value, lexer(), formatter)

    # Properly format line numbers when they show up in multi-line strings
    strcolor, _ = formatter.style_string['Token.Literal.String']
    intcolor, _ = formatter.style_string['Token.Literal.Number.Integer']
    value = re.sub(
        r'%s([0-9]+)' % re.escape(strcolor),
        lambda match: intcolor + match.group(1) + strcolor,
        value,
    )

    # Highlight the "current" line in yellow for visibility
    lineno = im_self.curframe.f_lineno

    value = re.sub(
        '(?<!\()%s%s[^\>]+>[^\[]+\[39m([^\x1b]+)[^m]+m([^\n]+)' % (re.escape(intcolor), lineno),
        lambda match: ''.join([
            str(lineno),
            ' ->',
            '\x1b[93m',
            match.group(1),
            re.sub('\x1b[^m]+m', '', match.group(2)),
            '\x1b[0m'
        ]),
        value
    )

    if filepart:
        _, first = filepart
        value = '\n'.join(value.splitlines()[-context:]) + '\n'

    if value.strip():
        old_stdout.write(value)
    im_self.stdout = old_stdout


class CustomPdb(Rdb):

    def cmdloop(self):
        self.do_list(tuple())
        return cmd.Cmd.cmdloop(self)

    def do_list(self, args):
        lines = 60
        context = (lines - 2) / 2
        if not args:
            first = max(1, self.curframe.f_lineno - context)
            last = first + context * 2 - 1
            args = "(%s, %s)" % (first, last)
        self.lineno = None
        with style(self, (
            self.curframe.f_code.co_filename, self.curframe.f_lineno - context)
        ):
            return Rdb.do_list(self, args)
    do_l = do_list

    def format_stack_entry(self, *args, **kwargs):
        entry = Rdb.format_stack_entry(self, *args, **kwargs)
        return '\n'.join(
            filter(lambda x: not x.startswith('->'), entry.splitlines())
        )

    def print_stack_entry(self, *args, **kwargs):
        with style(self):
            return Rdb.print_stack_entry(self, *args, **kwargs)

    def set_next(self, curframe):
        os.system('clear')
        Rdb.set_next(self, curframe)

    def set_return(self, arg):
        os.system('clear')
        Rdb.set_return(self, arg)

    def set_step(self):
        os.system('clear')
        Rdb.set_step(self)

    def default(self, line):
        with style(self):
            return Rdb.default(self, line)

    def parseline(self, line):
        line = line.strip()
        match = re.search('^([0-9]+)([a-zA-Z]+)', line)
        if match:
            times, command = match.group(1), match.group(2)
            line = command
            self.cmdqueue.extend(list(command * (int(times) - 1)))
        if line == '?':
            line = 'dir()'
        elif line.endswith('??'):
            line = "import inspect; print ''.join(inspect.getsourcelines(%s)[0][:25])" % line[:-2]
        elif line.endswith('?'):
            line = 'dir(%s)' % line[:-1]
        return cmd.Cmd.parseline(self, line)

    def displayhook(self, obj):
        if obj is not None and not isinstance(obj, list):
            return pprint.pprint(obj)
        return Rdb.displayhook(self, obj)

    def get_avail_port(self, *args, **kwargs):
        try:
            socket.gethostbyname('docker.for.mac.localhost')
            host = 'docker.for.mac.localhost'
        except:
            host = os.popen('ip route').read().split(' ')[2]
        sock, port = Rdb.get_avail_port(self, *args, **kwargs)
        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(
            str(port), (host, 6899)
        )
        return (sock, port)

    def say(self, m):
        logger.warning(m)


CustomPdb.complete = rlcompleter.Completer(locals()).complete


def set_trace():
    return CustomPdb().set_trace(sys._getframe().f_back)


def listen():
    queue = Queue()

    def _consume(queue):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 6899))
        print 'listening for rdb notifications on :6899...'
        while True:
            r, w, x = select.select([sock], [], [])
            for i in r:
                data = i.recv(1024)
                queue.put(data)
    worker = threading.Thread(target=_consume, args=(queue,))
    worker.setDaemon(True)
    worker.start()

    try:
        while True:
            try:
                port = queue.get(timeout=1)
                queue.task_done()
                if port == 'q':
                    break
                port = int(port)
                print 'opening telnet session at localhost:%d...' % port
                telnet(port)
                print 'listening for rdb notifications on :6899...'
            except Empty:
                pass
    except KeyboardInterrupt:
        print 'got Ctrl-C'
        queue.put('q')


def telnet(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    try:
        s.connect(('0.0.0.0', port))
    except:
        print 'unable to connect'
        return
    print 'connected to 0.0.0.0:%d' % port

    while True:
        socket_list = [sys.stdin, s]
        r, w, e = select.select(socket_list , [], [])
        for sock in r:
            if sock == s:
                data = sock.recv(4096)
                if not data:
                    print 'connection closed'
                    return
                else:
                    sys.stdout.write(data)
            else:
                msg = sys.stdin.readline()
                s.send(msg)


if __name__ == '__main__':
    listen()
