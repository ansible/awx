from __future__ import absolute_import

import sys
import traceback


class _Code(object):

    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name


class _Frame(object):
    Code = _Code

    def __init__(self, frame):
        self.f_globals = {
            "__file__": frame.f_globals.get("__file__", "__main__"),
            "__name__": frame.f_globals.get("__name__"),
            "__loader__": None,
        }
        self.f_locals = fl = {}
        try:
            fl["__traceback_hide__"] = frame.f_locals["__traceback_hide__"]
        except KeyError:
            pass
        self.f_code = self.Code(frame.f_code)
        self.f_lineno = frame.f_lineno


class _Object(object):

    def __init__(self, **kw):
        [setattr(self, k, v) for k, v in kw.items()]


class _Truncated(object):

    def __init__(self):
        self.tb_lineno = -1
        self.tb_frame = _Object(
            f_globals={"__file__": "",
                       "__name__": "",
                       "__loader__": None},
            f_fileno=None,
            f_code=_Object(co_filename="...",
                           co_name="[rest of traceback truncated]"),
        )
        self.tb_next = None


class Traceback(object):
    Frame = _Frame

    tb_frame = tb_lineno = tb_next = None
    max_frames = sys.getrecursionlimit() // 8

    def __init__(self, tb, max_frames=None, depth=0):
        limit = self.max_frames = max_frames or self.max_frames
        self.tb_frame = self.Frame(tb.tb_frame)
        self.tb_lineno = tb.tb_lineno
        if tb.tb_next is not None:
            if depth <= limit:
                self.tb_next = Traceback(tb.tb_next, limit, depth + 1)
            else:
                self.tb_next = _Truncated()


class ExceptionInfo(object):
    """Exception wrapping an exception and its traceback.

    :param exc_info: The exception info tuple as returned by
        :func:`sys.exc_info`.

    """

    #: Exception type.
    type = None

    #: Exception instance.
    exception = None

    #: Pickleable traceback instance for use with :mod:`traceback`
    tb = None

    #: String representation of the traceback.
    traceback = None

    #: Set to true if this is an internal error.
    internal = False

    def __init__(self, exc_info=None, internal=False):
        self.type, self.exception, tb = exc_info or sys.exc_info()
        try:
            self.tb = Traceback(tb)
            self.traceback = ''.join(
                traceback.format_exception(self.type, self.exception, tb),
            )
            self.internal = internal
        finally:
            del(tb)

    def __str__(self):
        return self.traceback

    def __repr__(self):
        return "<ExceptionInfo: %r>" % (self.exception, )

    @property
    def exc_info(self):
        return self.type, self.exception, self.tb
