class promise(object):
    """A promise.

    Evaluated when called or if the :meth:`evaluate` method is called.
    The function is evaluated on every access, so the value is not
    memoized (see :class:`mpromise`).

    Overloaded operations that will evaluate the promise:
        :meth:`__str__`, :meth:`__repr__`, :meth:`__cmp__`.

    """

    def __init__(self, fun, *args, **kwargs):
        self._fun = fun
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        return self.evaluate()

    def evaluate(self):
        return self._fun(*self._args, **self._kwargs)

    def __str__(self):
        return str(self())

    def __repr__(self):
        return repr(self())

    def __cmp__(self, rhs):
        if isinstance(rhs, self.__class__):
            return -cmp(rhs, self())
        return cmp(self(), rhs)

    def __eq__(self, rhs):
        return self() == rhs

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def __reduce__(self):
        return (self.__class__, (self._fun, ), {'_args': self._args,
                                                '_kwargs': self._kwargs})


def maybe_promise(value):
    """Evaluates if the value is a promise."""
    if isinstance(value, promise):
        return value.evaluate()
    return value
