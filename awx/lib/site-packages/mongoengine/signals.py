# -*- coding: utf-8 -*-

__all__ = ['pre_init', 'post_init', 'pre_save', 'pre_save_post_validation',
           'post_save', 'pre_delete', 'post_delete']

signals_available = False
try:
    from blinker import Namespace
    signals_available = True
except ImportError:
    class Namespace(object):
        def signal(self, name, doc=None):
            return _FakeSignal(name, doc)

    class _FakeSignal(object):
        """If blinker is unavailable, create a fake class with the same
        interface that allows sending of signals but will fail with an
        error on anything else.  Instead of doing anything on send, it
        will just ignore the arguments and do nothing instead.
        """

        def __init__(self, name, doc=None):
            self.name = name
            self.__doc__ = doc

        def _fail(self, *args, **kwargs):
            raise RuntimeError('signalling support is unavailable '
                               'because the blinker library is '
                               'not installed.')
        send = lambda *a, **kw: None
        connect = disconnect = has_receivers_for = receivers_for = \
            temporarily_connected_to = _fail
        del _fail

# the namespace for code signals.  If you are not mongoengine code, do
# not put signals in here.  Create your own namespace instead.
_signals = Namespace()

pre_init = _signals.signal('pre_init')
post_init = _signals.signal('post_init')
pre_save = _signals.signal('pre_save')
pre_save_post_validation = _signals.signal('pre_save_post_validation')
post_save = _signals.signal('post_save')
pre_delete = _signals.signal('pre_delete')
post_delete = _signals.signal('post_delete')
pre_bulk_insert = _signals.signal('pre_bulk_insert')
post_bulk_insert = _signals.signal('post_bulk_insert')
