import sys

class PasswordSetError(Exception):
    """Raised when the password can't be set.
    """

class PasswordDeleteError(Exception):
    """Raised when the password can't be deleted.
    """

class InitError(Exception):
    """Raised when the keyring could not be initialised
    """

class ExceptionRaisedContext(object):
    """
    An exception-trapping context that indicates whether an exception was
    raised.
    """
    def __init__(self, ExpectedException=Exception):
        self.ExpectedException = ExpectedException
        self.exc_info = None

    def __enter__(self):
        self.exc_info = object.__new__(ExceptionInfo)
        return self.exc_info

    def __exit__(self, *exc_info):
        self.exc_info.__init__(*exc_info)
        return self.exc_info.type and issubclass(
            self.exc_info.type, self.ExpectedException)

class ExceptionInfo(object):
    def __init__(self, *info):
        if not info:
            info = sys.exc_info()
        self.type, self.value, self.traceback = info

    def __bool__(self):
        """
        Return True if an exception occurred
        """
        return bool(self.type)

    __nonzero__ = __bool__
