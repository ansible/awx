from contextlib import contextmanager
import threading


_conf_settings = threading.local()


@contextmanager
def default_settings():
    """A context manager that will shut down database settings temporarily, for things like migrations"""
    try:
        previous_value = getattr(_conf_settings, 'db_settings_disabled', False)
        _conf_settings.db_settings_disabled = True
        yield
    finally:
        _conf_settings.db_settings_disabled = previous_value
