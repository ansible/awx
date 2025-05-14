import signal
import functools
import logging


logger = logging.getLogger('awx.main.tasks.signals')


__all__ = ['with_signal_handling', 'signal_callback']


class SignalExit(Exception):
    pass


class SignalState:
    # SIGTERM: Sent by supervisord to process group on shutdown
    # SIGUSR1: The dispatcherd cancel signal
    signals = (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1)

    def reset(self):
        for for_signal in self.signals:
            self.signal_flags[for_signal] = False
            self.original_methods[for_signal] = None

        self.is_active = False  # for nested context managers
        self.raise_exception = False

    def __init__(self):
        self.signal_flags = {}
        self.original_methods = {}
        self.reset()

    def raise_if_needed(self):
        if self.raise_exception:
            self.raise_exception = False  # so it is not raised a second time in error handling
            raise SignalExit()

    def set_signal_flag(self, *args, for_signal=None):
        self.signal_flags[for_signal] = True
        logger.info(f'Processed signal {for_signal}, set exit flag')
        self.raise_if_needed()

    def connect_signals(self):
        for for_signal in self.signals:
            self.original_methods[for_signal] = signal.getsignal(for_signal)
            signal.signal(for_signal, lambda *args, for_signal=for_signal: self.set_signal_flag(*args, for_signal=for_signal))
        self.is_active = True

    def restore_signals(self):
        for for_signal in self.signals:
            original_method = self.original_methods[for_signal]
            signal.signal(for_signal, original_method)
            # if we got a signal while context manager was active, call parent methods.
            if self.signal_flags[for_signal]:
                if callable(original_method):
                    try:
                        original_method()
                    except Exception as exc:
                        logger.info(f'Error processing original {for_signal} signal, error: {str(exc)}')
        self.reset()


signal_state = SignalState()


def signal_callback():
    return any(signal_state.signal_flags[for_signal] for for_signal in signal_state.signals)


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
