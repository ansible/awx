class LazyLoadDict(dict):
    """A dict subclass that calls a loader function on first read access.

    Writes (e.g. during the loading process itself) go straight through
    without triggering the loader.
    """

    def __init__(self, loader):
        super().__init__()
        self._loader = loader
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self._loaded = True
            self._loader()

    def __getitem__(self, key):
        self._ensure_loaded()
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._ensure_loaded()
        return super().get(key, default)

    def __contains__(self, key):
        self._ensure_loaded()
        return super().__contains__(key)

    def __iter__(self):
        self._ensure_loaded()
        return super().__iter__()

    def __len__(self):
        self._ensure_loaded()
        return super().__len__()

    def keys(self):
        self._ensure_loaded()
        return super().keys()

    def values(self):
        self._ensure_loaded()
        return super().values()

    def items(self):
        self._ensure_loaded()
        return super().items()

    def __bool__(self):
        self._ensure_loaded()
        return super().__bool__()

    def __repr__(self):
        self._ensure_loaded()
        return super().__repr__()

    def copy(self):
        self._ensure_loaded()
        return super().copy()

    def clear(self):
        super().clear()
        self._loaded = True
