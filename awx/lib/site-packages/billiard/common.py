# -*- coding: utf-8 -*-
"""
This module contains utilities added by billiard, to keep
"non-core" functionality out of ``.util``."""
from __future__ import absolute_import

import signal
import sys

from time import time
import pickle as pypickle
try:
    import cPickle as cpickle
except ImportError:  # pragma: no cover
    cpickle = None   # noqa

from .exceptions import RestartFreqExceeded

if sys.version_info < (2, 6):  # pragma: no cover
    # cPickle does not use absolute_imports
    pickle = pypickle
    pickle_load = pypickle.load
    pickle_loads = pypickle.loads
else:
    pickle = cpickle or pypickle
    pickle_load = pickle.load
    pickle_loads = pickle.loads

# cPickle.loads does not support buffer() objects,
# but we can just create a StringIO and use load.
if sys.version_info[0] == 3:
    from io import BytesIO
else:
    try:
        from cStringIO import StringIO as BytesIO  # noqa
    except ImportError:
        from StringIO import StringIO as BytesIO  # noqa

TERMSIGS = (
    'SIGHUP',
    'SIGQUIT',
    'SIGILL',
    'SIGTRAP',
    'SIGABRT',
    'SIGEMT',
    'SIGFPE',
    'SIGBUS',
    'SIGSEGV',
    'SIGSYS',
    'SIGPIPE',
    'SIGALRM',
    'SIGTERM',
    'SIGXCPU',
    'SIGXFSZ',
    'SIGVTALRM',
    'SIGPROF',
    'SIGUSR1',
    'SIGUSR2',
)


def pickle_loads(s, load=pickle_load):
    # used to support buffer objects
    return load(BytesIO(s))


def _shutdown_cleanup(signum, frame):
    sys.exit(-(256 - signum))


def reset_signals(handler=_shutdown_cleanup):
    for sig in TERMSIGS:
        try:
            signum = getattr(signal, sig)
            current = signal.getsignal(signum)
            if current is not None and current != signal.SIG_IGN:
                signal.signal(signum, handler)
        except (OSError, AttributeError, ValueError, RuntimeError):
            pass


class restart_state(object):
    RestartFreqExceeded = RestartFreqExceeded

    def __init__(self, maxR, maxT):
        self.maxR, self.maxT = maxR, maxT
        self.R, self.T = 0, None

    def step(self, now=None):
        now = time() if now is None else now
        R = self.R
        if self.T and now - self.T >= self.maxT:
            # maxT passed, reset counter and time passed.
            self.T, self.R = now, 0
        elif self.maxR and self.R >= self.maxR:
            # verify that R has a value as the result handler
            # resets this when a job is accepted. If a job is accepted
            # the startup probably went fine (startup restart burst
            # protection)
            if self.R:  # pragma: no cover
                pass
            self.R = 0  # reset in case someone catches the error
            raise self.RestartFreqExceeded("%r in %rs" % (R, self.maxT))
        # first run sets T
        if self.T is None:
            self.T = now
        self.R += 1
