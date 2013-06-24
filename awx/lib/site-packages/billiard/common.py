from __future__ import absolute_import

import signal
import sys

from time import time

from .exceptions import RestartFreqExceeded

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
