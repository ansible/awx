import signal
from contextlib import contextmanager

from awx.main.tasks.signals import signal_state, signal_callback, with_signal_handling


def do_nothing():
    do_nothing.called_count += 1


@contextmanager
def tmp_signals_for_test(func):
    """
    When we run our internal signal handlers, it will call the original signal
    handlers when its own work is finished.
    This would crash the test runners normally, because those methods will
    shut down the process.
    So this is a decorator to safely replace existing signal handlers
    with new signal handlers that do nothing so that tests do not crash.
    """

    def wrapper():
        original_sigterm = signal.getsignal(signal.SIGTERM)
        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGTERM, do_nothing)
        signal.signal(signal.SIGINT, do_nothing)
        do_nothing.called_count = 0
        func()
        signal.signal(signal.SIGTERM, original_sigterm)
        signal.signal(signal.SIGINT, original_sigint)

    return wrapper


@tmp_signals_for_test
def test_outer_inner_signal_handling():
    """
    Even if the flag is set in the outer context, its value should persist in the inner context
    """

    @with_signal_handling
    def f2():
        assert signal_callback()

    @with_signal_handling
    def f1():
        assert signal_callback() is False
        signal_state.set_flag()
        assert signal_callback()
        f2()

    original_sigterm = signal.getsignal(signal.SIGTERM)
    assert signal_callback() is False
    assert do_nothing.called_count == 0
    f1()
    assert signal_callback() is False
    assert signal.getsignal(signal.SIGTERM) is original_sigterm
    assert do_nothing.called_count == 1


@tmp_signals_for_test
def test_inner_outer_signal_handling():
    """
    Even if the flag is set in the inner context, its value should persist in the outer context
    """

    @with_signal_handling
    def f2():
        assert signal_callback() is False
        signal_state.set_flag()
        assert signal_callback()

    @with_signal_handling
    def f1():
        assert signal_callback() is False
        f2()
        assert signal_callback()

    original_sigterm = signal.getsignal(signal.SIGTERM)
    assert signal_callback() is False
    assert do_nothing.called_count == 0
    f1()
    assert signal_callback() is False
    assert signal.getsignal(signal.SIGTERM) is original_sigterm
    assert do_nothing.called_count == 1
