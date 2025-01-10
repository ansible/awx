from contextlib import ContextDecorator

from .lazy import settings as db_settings


class FakeSettings:
    def __init__(self, overrides, original):
        self.overrides = overrides
        self.original = original

    def __getattr__(self, name):
        if name in self.overrides:
            return self.overrides[name]
        return getattr(self.original, name)


class override_db_settings(ContextDecorator):
    """Context manager to apply temporary values for database settings"""

    def __init__(self, **settings):
        self.settings = settings
        self._original = None

    def __enter__(self):
        self._original = db_settings._wrapped
        db_settings._wrapped = FakeSettings(self.settings, self._original)

    def __exit__(self, exc_type, exc_value, traceback):
        db_settings._wrapped = self._original
        self._original = None
        return False  # for not suppressing exceptions
