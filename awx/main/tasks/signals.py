import signal
import functools
import logging


logger = logging.getLogger('awx.main.tasks.signals')


__all__ = ['with_signal_handling', 'signal_callback']


class SignalExit(Exception):
    pass


class SignalState:
    def reset(self):
        self.sigterm_flag = False
        self.is_active = False
        self.original_sigterm = None
        self.original_sigint = None
        self.raise_exception = False

    def __init__(self):
        self.reset()

    def set_flag(self, *args):
        """Method to pass into the python signal.signal method to receive signals"""
        self.sigterm_flag = True
        if self.raise_exception:
            self.raise_exception = False  # so it is not raised a second time in error handling
            raise SignalExit()

    def connect_signals(self):
        self.original_sigterm = signal.getsignal(signal.SIGTERM)
        self.original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGTERM, self.set_flag)
        signal.signal(signal.SIGINT, self.set_flag)
        self.is_active = True

    def restore_signals(self):
        signal.signal(signal.SIGTERM, self.original_sigterm)
        signal.signal(signal.SIGINT, self.original_sigint)
        self.reset()


signal_state = SignalState()


def signal_callback():
    return signal_state.sigterm_flag


def with_signal_handling(f):
    """
    Change signal handling to make signal_callback return True in event of SIGTERM or SIGINT.
    """

    @functools.wraps(f)
    def _wrapped(*args, **kwargs):
        try:
            this_is_outermost_caller = False
            if not signal_state.is_active:
                signal_state.connect_signals()
                this_is_outermost_caller = True
            return f(*args, **kwargs)
        finally:
            if this_is_outermost_caller:
                signal_state.restore_signals()

    return _wrapped
