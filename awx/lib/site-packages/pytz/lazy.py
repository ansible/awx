from threading import RLock
try:
    from UserDict import DictMixin
except ImportError:
    from collections import Mapping as DictMixin


_fill_lock = RLock()


class LazyDict(DictMixin):
    """Dictionary populated on first use."""
    data = None
    def __getitem__(self, key):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return self.data[key.upper()]

    def __contains__(self, key):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock_release()
        return key in self.data

    def __iter__(self):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return iter(self.data)

    def __len__(self):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return len(self.data)

    def keys(self):
        if self.data is None:
            _fill_lock.acquire()
            try:
                if self.data is None:
                    self._fill()
            finally:
                _fill_lock.release()
        return self.data.keys()


class LazyList(list):
    """List populated on first use."""
    def __new__(cls, fill_iter):

        class LazyList(list):
            _fill_iter = None

        _props = (
            '__str__', '__repr__', '__unicode__',
            '__hash__', '__sizeof__', '__cmp__', '__nonzero__',
            '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',
            'append', 'count', 'index', 'extend', 'insert', 'pop', 'remove',
            'reverse', 'sort', '__add__', '__radd__', '__iadd__', '__mul__',
            '__rmul__', '__imul__', '__contains__', '__len__', '__nonzero__',
            '__getitem__', '__setitem__', '__delitem__', '__iter__',
            '__reversed__', '__getslice__', '__setslice__', '__delslice__')

        def lazy(name):
            def _lazy(self, *args, **kw):
                if self._fill_iter is not None:
                    _fill_lock.acquire()
                    try:
                        if self._fill_iter is not None:
                            list.extend(self, self._fill_iter)
                            self._fill_iter = None
                    finally:
                        _fill_lock.release()
                real = getattr(list, name)
                setattr(self.__class__, name, real)
                return real(self, *args, **kw)
            return _lazy

        for name in _props:
            setattr(LazyList, name, lazy(name))

        new_list = LazyList()
        new_list._fill_iter = fill_iter
        return new_list


class LazySet(set):
    """Set populated on first use."""
    def __new__(cls, fill_iter):

        class LazySet(set):
            _fill_iter = None

        _props = (
            '__str__', '__repr__', '__unicode__',
            '__hash__', '__sizeof__', '__cmp__', '__nonzero__',
            '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',
            '__contains__', '__len__', '__nonzero__',
            '__getitem__', '__setitem__', '__delitem__', '__iter__',
            '__sub__', '__and__', '__xor__', '__or__',
            '__rsub__', '__rand__', '__rxor__', '__ror__',
            '__isub__', '__iand__', '__ixor__', '__ior__',
            'add', 'clear', 'copy', 'difference', 'difference_update',
            'discard', 'intersection', 'intersection_update', 'isdisjoint',
            'issubset', 'issuperset', 'pop', 'remove',
            'symmetric_difference', 'symmetric_difference_update',
            'union', 'update')

        def lazy(name):
            def _lazy(self, *args, **kw):
                if self._fill_iter is not None:
                    _fill_lock.acquire()
                    try:
                        if self._fill_iter is not None:
                            for i in self._fill_iter:
                                set.add(self, i)
                            self._fill_iter = None
                    finally:
                        _fill_lock.release()
                real = getattr(set, name)
                setattr(self.__class__, name, real)
                return real(self, *args, **kw)
            return _lazy

        for name in _props:
            setattr(LazySet, name, lazy(name))

        new_set = LazySet()
        new_set._fill_iter = fill_iter
        return new_set
