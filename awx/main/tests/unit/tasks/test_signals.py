import signal

from awx.main.tasks.signals import signal_state, signal_callback, with_signal_handling


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
    f1()
    assert signal_callback() is False
    assert signal.getsignal(signal.SIGTERM) is original_sigterm


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
    f1()
    assert signal_callback() is False
    assert signal.getsignal(signal.SIGTERM) is original_sigterm
